from __future__ import annotations

import datetime
from collections import defaultdict

from sqlalchemy.orm import Session

from backend.database.schemas import Property, PropertyTransaction, PropertyValuationSnapshot, RentalLeasePeriod
from backend.portfolio.valuation import active_engine, value_property
from backend.sentiment.sentiment_api import fetch_market_sentiment, get_overall_sentiment, get_sentiment

CAPITAL_COST_TYPES = {"acquisition_cost", "capital_improvement"}
RENTAL_INCOME_TYPES = {"rental_income"}
OPERATING_EXPENSE_TYPES = {
    "maintenance", "management_fee", "rates_taxes", "insurance", "operating_expense",
}
ALLOWED_TRANSACTION_TYPES = CAPITAL_COST_TYPES | RENTAL_INCOME_TYPES | OPERATING_EXPENSE_TYPES | {
    "sale_cost", "sale_proceeds",
}


def _empty_summary(sentiment: str = "unknown") -> dict:
    return {
        "portfolio_value": 0,
        "total_investment": 0,
        "cost_basis": 0,
        "growth_percentage": 0,
        "total_profit": 0,
        "unrealized_capital_gain": 0,
        "cumulative_net_rental_income": 0,
        "total_return_lkr": 0,
        "monthly_rental_income": 0,
        "property_mix": {"housing": 0, "rental": 0, "land": 0},
        "sentiment": sentiment,
        "valuation_engine": active_engine(),
    }


def _transactions_by_property(db: Session, properties: list[Property]) -> dict[int, list[PropertyTransaction]]:
    ids = [prop.id for prop in properties]
    if not ids:
        return {}
    grouped: dict[int, list[PropertyTransaction]] = defaultdict(list)
    for transaction in db.query(PropertyTransaction).filter(PropertyTransaction.property_id.in_(ids)).all():
        grouped[transaction.property_id].append(transaction)
    return grouped


def _calendar_months(start: datetime.date, end: datetime.date) -> int:
    """Count inclusive calendar months, because rent is agreed monthly."""
    if end < start:
        return 0
    return (end.year - start.year) * 12 + end.month - start.month + 1


def _seed_or_get_lease_periods(db: Session, prop: Property) -> list[RentalLeasePeriod]:
    if prop.property_type != "rental" or not prop.rental:
        return []
    periods = db.query(RentalLeasePeriod).filter(
        RentalLeasePeriod.property_id == prop.id
    ).order_by(RentalLeasePeriod.lease_start_date).all()
    if periods:
        return periods
    if not prop.rental.lease_start_date or not prop.rental.monthly_rent:
        return []
    # Read legacy rentals as one period without mutating the database during a
    # GET. New periods are persisted by the create/update property services.
    period = RentalLeasePeriod(
        property_id=prop.id,
        monthly_rent=prop.rental.monthly_rent,
        lease_start_date=prop.rental.lease_start_date,
        lease_end_date=prop.rental.lease_end_date,
    )
    return [period]


def _lease_income_to_date(db: Session, prop: Property, as_of: datetime.date) -> tuple[float, int]:
    periods = _seed_or_get_lease_periods(db, prop)
    if not periods:
        return 0.0, 0
    total = 0.0
    months = 0
    for period in periods:
        period_end = min(period.lease_end_date or as_of, as_of)
        if period_end < period.lease_start_date:
            continue
        count = _calendar_months(period.lease_start_date, period_end)
        total += float(period.monthly_rent or 0.0) * count
        months += count
    return total, months


def _financials(prop: Property, transactions: list[PropertyTransaction], db: Session | None = None, as_of: datetime.date | None = None) -> dict:
    purchase_price_per_perch = None
    if getattr(prop, "property_type", None) == "land" and getattr(prop, "land", None) and prop.land.land_size:
        purchase_price_per_perch = float(prop.purchase_price or 0.0)
        purchase_price = purchase_price_per_perch * float(prop.land.land_size)
    else:
        purchase_price = float(prop.purchase_price or 0.0)
    acquisition_costs = float(prop.acquisition_costs or 0.0)
    improvements = float(prop.capital_improvements or 0.0)
    rental_income = 0.0
    operating_expenses = 0.0
    ledger_sale_costs = 0.0
    ledger_sale_proceeds = 0.0

    for item in transactions:
        amount = float(item.amount or 0.0)
        if item.transaction_type == "acquisition_cost":
            acquisition_costs += amount
        elif item.transaction_type == "capital_improvement":
            improvements += amount
        elif item.transaction_type in RENTAL_INCOME_TYPES:
            rental_income += amount
        elif item.transaction_type in OPERATING_EXPENSE_TYPES:
            operating_expenses += amount
        elif item.transaction_type == "sale_cost":
            ledger_sale_costs += amount
        elif item.transaction_type == "sale_proceeds":
            ledger_sale_proceeds += amount

    cost_basis = purchase_price + acquisition_costs + improvements
    lease_income = 0.0
    lease_months = 0
    if db is not None and as_of is not None and getattr(prop, "property_type", None) == "rental":
        lease_income, lease_months = _lease_income_to_date(db, prop, as_of)
    rental_income = lease_income or rental_income
    net_rental = rental_income - operating_expenses
    sale_price = float(prop.sale_price or ledger_sale_proceeds or 0.0)
    selling_costs = float(prop.selling_costs or 0.0) + ledger_sale_costs
    realized_gain = sale_price - selling_costs - cost_basis if sale_price else None
    return {
        "purchase_price": purchase_price,
        "purchase_price_per_perch": purchase_price_per_perch,
        "acquisition_costs": acquisition_costs,
        "capital_improvements": improvements,
        "cost_basis": cost_basis,
        "cumulative_rental_income": rental_income,
        "cumulative_operating_expenses": operating_expenses,
        "cumulative_net_rental_income": net_rental,
        "rental_income_to_date": rental_income,
        "rental_months_to_date": lease_months,
        "sale_price": sale_price or None,
        "selling_costs": selling_costs,
        "realized_gain": realized_gain,
    }


def calculate_portfolio(db: Session, user_id: int, valuation_date: datetime.date | None = None):
    """Value a portfolio and keep capital, income, and realized returns distinct."""
    valuation_date = valuation_date or datetime.date.today()
    overall_sentiment = "unknown"
    sentiment_dict = None
    engine = active_engine()

    try:
        properties = db.query(Property).filter(Property.user_id == user_id).all()
        transactions = _transactions_by_property(db, properties)

        try:
            sentiment_dict = fetch_market_sentiment()
            overall_sentiment = get_overall_sentiment(sentiment_dict)
        except Exception:
            overall_sentiment = "unknown"

        totals = defaultdict(float)
        mix = {"housing": 0, "rental": 0, "land": 0}
        detailed = []

        for prop in properties:
            try:
                valuation = value_property(prop, engine=engine, db=db, valuation_date=valuation_date)
                financial = _financials(prop, transactions.get(prop.id, []), db=db, as_of=valuation_date)
                current_value = valuation.capital_value
                is_sold = bool(financial["sale_price"] or str(prop.status or "").lower() == "sold")

                unrealized_gain = (
                    current_value - financial["cost_basis"]
                    if current_value is not None and not is_sold else None
                )
                total_return = (
                    (financial["realized_gain"] if is_sold else unrealized_gain) or 0.0
                ) + financial["cumulative_net_rental_income"]

                if not is_sold:
                    totals["cost_basis"] += financial["cost_basis"]
                    if current_value is not None:
                        totals["portfolio_value"] += current_value
                    if unrealized_gain is not None:
                        totals["unrealized_gain"] += unrealized_gain
                if valuation.monthly_income:
                    totals["monthly_income"] += valuation.monthly_income
                totals["net_rental"] += financial["cumulative_net_rental_income"]
                totals["total_return"] += total_return

                if prop.property_type in mix and not is_sold:
                    mix[prop.property_type] += 1

                try:
                    sentiment = get_sentiment(sentiment_dict, prop.property_type, "medium_term")
                except Exception:
                    sentiment = {"value": 0.0, "label": "unknown"}

                detailed.append({
                    "property_id": prop.id,
                    "created_at": prop.created_at,
                    "purchase_date": prop.purchase_date,
                    "type": prop.property_type,
                    "location": prop.location,
                    "district": prop.district,
                    "status": prop.status,
                    "current_value": current_value,
                    "profit": unrealized_gain,
                    "unrealized_capital_gain": unrealized_gain,
                    "unrealized_gain_pct": (
                        unrealized_gain / financial["cost_basis"] * 100.0
                        if unrealized_gain is not None and financial["cost_basis"] else None
                    ),
                    "total_return_lkr": total_return,
                    "sentiment": sentiment.get("label", "unknown"),
                    **financial,
                    **valuation.as_dict(),
                })
            except Exception as exc:
                print(f"Error processing property {prop.id}: {exc}")

        growth = (
            totals["unrealized_gain"] / totals["cost_basis"] * 100.0
            if totals["cost_basis"] else 0.0
        )
        summary = {
            "portfolio_value": round(totals["portfolio_value"], 2),
            "total_investment": round(totals["cost_basis"], 2),
            "cost_basis": round(totals["cost_basis"], 2),
            "growth_percentage": round(growth, 2),
            "total_profit": round(totals["unrealized_gain"], 2),
            "unrealized_capital_gain": round(totals["unrealized_gain"], 2),
            "cumulative_net_rental_income": round(totals["net_rental"], 2),
            "total_return_lkr": round(totals["total_return"], 2),
            "monthly_rental_income": round(totals["monthly_income"], 2),
            "property_mix": mix,
            "sentiment": overall_sentiment,
            "valuation_engine": engine,
            "requested_valuation_date": valuation_date.isoformat(),
        }
        return {"summary": summary, "properties": detailed}
    except Exception as exc:
        print(f"Error in calculate_portfolio: {exc}")
        return {"summary": _empty_summary(overall_sentiment), "properties": []}


def add_property_transaction(db: Session, user_id: int, property_id: int, data):
    prop = db.query(Property).filter(Property.id == property_id, Property.user_id == user_id).first()
    if not prop:
        raise ValueError("Property not found")
    transaction_type = data.transaction_type.strip().lower()
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")
    transaction = PropertyTransaction(
        property_id=property_id,
        transaction_date=data.transaction_date,
        transaction_type=transaction_type,
        amount=data.amount,
        description=data.description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def list_property_transactions(db: Session, user_id: int, property_id: int):
    exists = db.query(Property.id).filter(Property.id == property_id, Property.user_id == user_id).first()
    if not exists:
        raise ValueError("Property not found")
    return db.query(PropertyTransaction).filter(
        PropertyTransaction.property_id == property_id
    ).order_by(PropertyTransaction.transaction_date).all()


def snapshot_portfolio(db: Session, user_id: int, valuation_date: datetime.date | None = None):
    valuation_date = valuation_date or datetime.date.today()
    data = calculate_portfolio(db, user_id, valuation_date=valuation_date)
    saved = []
    created = 0
    for row in data["properties"]:
        value = row.get("estimated_current_value")
        if value is None or not row.get("feature_hash"):
            continue
        as_of = datetime.date.fromisoformat(row["valuation_as_of"] or valuation_date.isoformat())
        model_version = row.get("model_version") or "legacy"
        index_version = row.get("index_version") or "none"
        snapshot = db.query(PropertyValuationSnapshot).filter_by(
            property_id=row["property_id"],
            valuation_as_of=as_of,
            model_version=model_version,
            index_version=index_version,
        ).first()
        if snapshot is None:
            value_range = row.get("value_range") or {}
            provenance = row.get("valuation_provenance") or {}
            index = provenance.get("index") or {}
            snapshot = PropertyValuationSnapshot(
                property_id=row["property_id"], valuation_as_of=as_of,
                estimated_value=value, lower_value=value_range.get("lower"),
                upper_value=value_range.get("upper"), status=row.get("valuation_status") or "unknown",
                method=row.get("valuation_method") or "unknown",
                confidence=row.get("valuation_confidence") or "low",
                model_version=model_version, model_anchor=row.get("model_anchor"),
                index_version=index_version, index_source=index.get("source"),
                index_segment=index.get("segment"), index_geography=index.get("geography"),
                index_observation=index.get("observation"), index_factor=row.get("index_factor"),
                feature_hash=row["feature_hash"], provenance=provenance,
                reasons=row.get("valuation_notes") or [],
            )
            db.add(snapshot)
            created += 1
        saved.append(snapshot)
    db.commit()
    return {
        "valuation_date": valuation_date,
        "snapshots_created": created,
        "snapshots_considered": len(saved),
    }


def list_valuation_snapshots(db: Session, user_id: int, property_id: int):
    exists = db.query(Property.id).filter(Property.id == property_id, Property.user_id == user_id).first()
    if not exists:
        raise ValueError("Property not found")
    return db.query(PropertyValuationSnapshot).filter(
        PropertyValuationSnapshot.property_id == property_id
    ).order_by(PropertyValuationSnapshot.valuation_as_of.desc()).all()

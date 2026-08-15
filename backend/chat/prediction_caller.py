from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.dynamic.services import make_prediction, get_property_recommendation


def format_currency_lkr(val: float) -> str:
    if val >= 10_000_000:
        return f"LKR {val / 1_000_000:.2f}M"
    elif val >= 100_000:
        return f"LKR {val / 100_000:.2f} Lakhs"
    else:
        return f"LKR {round(val):,}"


def run_full_property_analysis(
    db: Session,
    model_type: str,
    input_features: Dict[str, Any],
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes:
    1. Core ML Model prediction (LightGBM/CatBoost)
    2. LSTM forward projection trajectory
    3. RL Agent recommendation (BUY/HOLD/SELL)
    """
    clean_model_type = (model_type or "house").strip().lower()
    if clean_model_type not in ("house", "land", "rental"):
        clean_model_type = "house"

    # 1. Prediction with dynamic service (handles ML model + LSTM projection + index anchor)
    pred_res = make_prediction(
        db=db,
        model_type=clean_model_type,
        input_features=input_features,
        user_id=user_id,
    )

    predicted_val = float(pred_res.get("predicted_value", 0.0))
    sequence = [float(v) for v in pred_res.get("predicted_sequence", [])]
    unit = pred_res.get("unit") or ("LKR_per_perch" if clean_model_type == "land" else "LKR_per_month" if clean_model_type == "rental" else "LKR_total")
    confidence = pred_res.get("confidence") or "medium"
    details = pred_res.get("details") or {}

    # Format price and range
    unit_suffix = ""
    if clean_model_type == "land":
        unit_suffix = " / perch"
    elif clean_model_type == "rental":
        unit_suffix = " / month"

    price_str = f"LKR {round(predicted_val):,}{unit_suffix}"
    low_range = predicted_val * 0.9
    high_range = predicted_val * 1.1

    if clean_model_type == "rental":
        range_str = f"LKR {round(low_range):,} - {round(high_range):,}{unit_suffix}"
    else:
        range_str = f"{format_currency_lkr(low_range)} - {format_currency_lkr(high_range)}{unit_suffix}"

    # Whole plot value for land if available
    total_value_str = None
    if clean_model_type == "land" and pred_res.get("total_value"):
        total_value_str = f"LKR {round(float(pred_res['total_value'])):,}"

    # 2. RL Recommendation
    rl_res = get_property_recommendation(db, user_id, clean_model_type)
    raw_rec = str(rl_res.get("recommendation") or "HOLD").upper()
    if "BUY" in raw_rec:
        rec_label = "BUY"
    elif "SELL" in raw_rec:
        rec_label = "SELL"
    elif "HOLD" in raw_rec:
        rec_label = "HOLD"
    else:
        rec_label = raw_rec

    # Generate reasoning
    location_name = input_features.get("sub_location") or input_features.get("location") or input_features.get("location_text") or input_features.get("district") or "this area"
    district_name = input_features.get("district") or ""
    full_loc = f"{location_name}, {district_name}".strip(", ")

    reasoning_parts = []
    if clean_model_type == "house":
        sqft = input_features.get("house_sqft") or input_features.get("house_sqft_capped")
        beds = input_features.get("bedrooms")
        baths = input_features.get("bathrooms")
        reasoning_parts.append(f"Estimated for a {beds}BR/{baths}BA property (~{sqft} sqft) in {full_loc}.")
    elif clean_model_type == "land":
        perches = input_features.get("land_size")
        reasoning_parts.append(f"Estimated for a {perches} perch land parcel in {full_loc}.")
    elif clean_model_type == "rental":
        p_type = input_features.get("property_type", "property")
        furn = input_features.get("furnishing_status", "unfurnished")
        reasoning_parts.append(f"Estimated monthly rent for a {furn} {p_type.lower()} in {full_loc}.")

    reasoning_parts.append(f"Market index signals indicate {confidence} confidence with {rec_label} recommendation based on recent price momentum.")
    reasoning_text = " ".join(reasoning_parts)

    return {
        "model_type": clean_model_type,
        "predicted_value": predicted_val,
        "price": price_str,
        "range": range_str,
        "unit": unit,
        "total_value": total_value_str,
        "confidence": confidence,
        "lstm_sequence": sequence,
        "lstm_labels": ["Q1", "Q2", "Q3", "Q4", "Q5"] if len(sequence) == 5 else [f"P{i+1}" for i in range(len(sequence))],
        "rl_recommendation": rec_label,
        "reasoning": reasoning_text,
        "location": full_loc,
        "features": input_features,
        "details": details,
    }

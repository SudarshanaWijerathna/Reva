import datetime
import unittest
from dataclasses import dataclass
from unittest.mock import patch

from backend.portfolio import valuation as V
from backend.portfolio import valuation_v2 as V2
from backend.portfolio.payloads import build_land_payload
from backend.portfolio.service import _calendar_months, _financials
from backend.predictions import market_index


@dataclass
class CompleteLand:
    land_size: float = 10.0
    zoning_type: str = "residential"
    road_access: str = "main road"
    electricity: bool | None = None
    water: bool | None = None
    clear_deed: bool | None = None
    bank_loan: bool | None = None
    near_town: bool | None = None
    distance_to_town_m: float | None = None


@dataclass
class CompleteHouse:
    land_size_perches: float = 10.0
    house_size_sqft: float = 1800.0
    bedrooms: int = 3
    bathrooms: int = 2
    floors: int = 2
    built_year: int = 2018
    property_condition: str = "good"
    parking_spaces: int = 1
    road_width_ft: float = 20.0
    water_available: bool = True
    electricity_available: bool = True
    description: str = "Residential family house"


@dataclass
class CompleteRental:
    monthly_rent: float = 120_000.0
    occupancy_status: str = "occupied"
    tenant_type: str = "family"
    property_subtype: str = "House"
    bedrooms: int = 3
    bathrooms: int = 2
    floor_area_sqft: float = 1800.0
    land_size_perches: float = 10.0
    furnishing_status: str = "unfurnished"
    parking_spaces: int = 1
    vacancy_rate: float = 0.05
    monthly_maintenance: float = 10_000.0
    monthly_management_fees: float = 0.0
    annual_rates_taxes: float = 24_000.0
    annual_insurance: float = 12_000.0
    annual_other_expenses: float = 0.0


@dataclass
class Property:
    id: int
    property_type: str
    location: str
    district: str | None
    purchase_price: float
    locality: str | None = None
    latitude: float | None = 6.9271
    longitude: float | None = 79.8612
    land: CompleteLand | None = None
    housing: CompleteHouse | None = None
    rental: CompleteRental | None = None
    status: str = "Active"


def usable_factor(asset: str, value: float = 1.10):
    return market_index.GrowthFactor(
        value=value,
        confidence=market_index.Confidence.HIGH,
        asset=asset,
        anchor_month="2025-12",
        target_month="2026-03",
    )


class PayloadTests(unittest.TestCase):
    def test_missing_land_features_are_not_fabricated_as_true(self):
        prop = Property(1, "land", "Colombo 5", "Colombo", 10_000_000, land=CompleteLand())
        build = build_land_payload(prop)
        self.assertIsNotNone(build.payload)
        for name in ("electricity", "water", "clear_deed", "bank_loan", "near_town"):
            self.assertNotIn(name, build.payload)
            self.assertIn(name, build.missing)

    def test_unknown_district_blocks_the_model_path(self):
        prop = Property(1, "land", "Imbulgoda", None, 10_000_000, land=CompleteLand())
        build = build_land_payload(prop)
        self.assertIsNone(build.payload)
        self.assertIn("district", build.missing)


class CurrentValueTests(unittest.TestCase):
    @patch.object(V2, "_observed_factor", return_value=usable_factor("house"))
    @patch.object(V2, "_predict", return_value={"predicted_value": 50_000_000.0})
    @patch.object(V2, "model_manifest", return_value={
        "model_version": "house:test", "anchor_month": "2025-12", "model_variant": "test"
    })
    def test_house_current_value_is_anchor_times_observed_factor(self, _manifest, _predict, _factor):
        prop = Property(2, "housing", "Colombo 5", "Colombo", 30_000_000, housing=CompleteHouse())
        result = V.value_property(prop, engine=V.HYBRID, valuation_date=datetime.date(2026, 8, 1))
        self.assertEqual(result.capital_value, 55_000_000.0)
        self.assertEqual(result.valuation_as_of, datetime.date(2026, 3, 31))
        self.assertEqual(result.valuation_status, "observed_index")
        self.assertEqual(result.method, "house_avm_x_observed_index")

    @patch.object(V2, "_predict", return_value={
        "total_value": 20_000_000.0, "confidence": "high"
    })
    @patch.object(V2, "model_manifest", return_value={
        "model_version": "land:test", "anchor_month": "2025-12", "model_variant": "test"
    })
    def test_non_colombo_property_is_anchor_only(self, _manifest, _predict):
        prop = Property(3, "land", "Imbulgoda", "Gampaha", 8_000_000, land=CompleteLand())
        result = V.value_property(prop, engine=V.HYBRID, valuation_date=datetime.date(2026, 8, 1))
        self.assertEqual(result.capital_value, 20_000_000.0)
        self.assertEqual(result.valuation_status, "anchor_only")
        self.assertEqual(result.valuation_as_of, datetime.date(2025, 12, 31))
        self.assertTrue(any("covers Colombo" in note for note in result.notes))


class RentalReconciliationTests(unittest.TestCase):
    @patch.object(V2, "_observed_factor", return_value=usable_factor("house", 1.0))
    @patch.object(V2, "_predict")
    @patch.object(V2, "model_manifest", return_value={
        "model_version": "house:test", "anchor_month": "2025-12", "model_variant": "test"
    })
    def test_rental_separates_rent_noi_and_capital_value(self, _manifest, predict, _factor):
        predict.side_effect = [
            {"predicted_value": 125_000.0, "details": {}},
            {"predicted_value": 30_000_000.0},
        ]
        prop = Property(4, "rental", "Colombo 5", "Colombo", 25_000_000, rental=CompleteRental())
        result = V.value_property(prop, engine=V.HYBRID, valuation_date=datetime.date(2026, 8, 1))
        expected_noi = 120_000 * 12 * 0.95 - 10_000 * 12 - 24_000 - 12_000
        income_value = expected_noi / V2.DEFAULT_CAP_RATE
        self.assertAlmostEqual(result.annual_net_operating_income, expected_noi)
        self.assertEqual(result.monthly_income, 120_000)
        self.assertNotEqual(result.capital_value, result.monthly_income)
        self.assertEqual(result.capital_value, round(30_000_000 * 0.6 + income_value * 0.4, 2))
        self.assertEqual(result.method, "rental_market_income_reconciled")


class AccountingTests(unittest.TestCase):
    @dataclass
    class Tx:
        transaction_type: str
        amount: float

    def test_cost_basis_and_net_rent_are_distinct(self):
        prop = type("P", (), {
            "purchase_price": 10_000_000,
            "acquisition_costs": 500_000,
            "capital_improvements": 1_000_000,
            "sale_price": None,
            "selling_costs": 0,
        })()
        rows = [
            self.Tx("capital_improvement", 250_000),
            self.Tx("rental_income", 600_000),
            self.Tx("maintenance", 100_000),
        ]
        result = _financials(prop, rows)
        self.assertEqual(result["cost_basis"], 11_750_000)
        self.assertEqual(result["cumulative_net_rental_income"], 500_000)

    def test_land_purchase_price_is_converted_from_perch_to_total(self):
        prop = type("P", (), {
            "property_type": "land",
            "purchase_price": 1_000_000,
            "land": type("L", (), {"land_size": 15})(),
            "acquisition_costs": 0,
            "capital_improvements": 0,
            "sale_price": None,
            "selling_costs": 0,
        })()
        result = _financials(prop, [])
        self.assertEqual(result["purchase_price"], 15_000_000)
        self.assertEqual(result["purchase_price_per_perch"], 1_000_000)
        self.assertEqual(result["cost_basis"], 15_000_000)

    def test_rent_uses_inclusive_calendar_months(self):
        self.assertEqual(
            _calendar_months(datetime.date(2026, 1, 20), datetime.date(2026, 3, 2)),
            3,
        )


if __name__ == "__main__":
    unittest.main()

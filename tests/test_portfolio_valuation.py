"""
Tests for portfolio valuation.

The bug these exist to prevent: summing quantities that are not the same kind of
thing. ``portfolio_value`` previously added land prices quoted *per perch*,
*monthly rents*, and house *sale prices* into a single total.
"""

import os
import unittest
from dataclasses import dataclass

from backend.portfolio import valuation as V


@dataclass
class Land:
    land_size: float
    zoning_type: str = "Residential"
    road_access: str = "Main road"


@dataclass
class Housing:
    land_size_perches: float
    house_size_sqft: float
    floors: int = 2
    built_year: int = 2015
    property_condition: str = "Good"


@dataclass
class Rental:
    monthly_rent: float
    occupancy_status: str = "Occupied"
    tenant_type: str = "Family"


@dataclass
class Prop:
    id: int
    property_type: str
    location: str
    purchase_price: float
    land: Land | None = None
    housing: Housing | None = None
    rental: Rental | None = None
    status: str = "Active"


LAND_40 = Prop(1, "land", "Colombo", 30_000_000, land=Land(land_size=40.0))
LAND_10 = Prop(2, "land", "Colombo", 8_000_000, land=Land(land_size=10.0))
HOUSE = Prop(3, "housing", "Colombo", 45_000_000, housing=Housing(15, 2200))
RENTAL = Prop(4, "rental", "Colombo", 25_000_000, rental=Rental(monthly_rent=120_000))


class EngineSelectionTests(unittest.TestCase):
    def test_the_default_engine_is_legacy(self):
        """Nothing a user has already seen may move until an engine is chosen."""
        original = os.environ.pop("PORTFOLIO_VALUATION_ENGINE", None)
        try:
            self.assertEqual(V.active_engine(), V.LEGACY)
        finally:
            if original is not None:
                os.environ["PORTFOLIO_VALUATION_ENGINE"] = original

    def test_an_unknown_engine_falls_back_to_legacy(self):
        original = os.environ.get("PORTFOLIO_VALUATION_ENGINE")
        os.environ["PORTFOLIO_VALUATION_ENGINE"] = "quantum"
        try:
            self.assertEqual(V.active_engine(), V.LEGACY)
        finally:
            if original is None:
                os.environ.pop("PORTFOLIO_VALUATION_ENGINE", None)
            else:
                os.environ["PORTFOLIO_VALUATION_ENGINE"] = original


class UnitCorrectnessTests(unittest.TestCase):
    """Every value entering portfolio_value must be a capital value in LKR."""

    def test_land_scales_with_plot_size(self):
        small = V.value_property(LAND_10, engine=V.SCRAPER_FIXED).capital_value
        large = V.value_property(LAND_40, engine=V.SCRAPER_FIXED).capital_value
        self.assertAlmostEqual(large / small, 4.0, places=6,
                               msg="A 40-perch plot must be worth four times a 10-perch one.")

    def test_legacy_ignores_plot_size(self):
        """Documents the bug, so a regression back to it is visible."""
        small = V.value_property(LAND_10, engine=V.LEGACY).capital_value
        large = V.value_property(LAND_40, engine=V.LEGACY).capital_value
        self.assertEqual(small, large)

    def test_rent_is_capitalised_not_counted_as_capital(self):
        legacy = V.value_property(RENTAL, engine=V.LEGACY)
        fixed = V.value_property(RENTAL, engine=V.SCRAPER_FIXED)

        self.assertGreater(
            fixed.capital_value,
            10 * legacy.capital_value,
            "A capitalised rent must be far larger than the monthly rent itself.",
        )
        self.assertEqual(fixed.monthly_income, 120_000)

    def test_capitalisation_uses_a_plausible_yield(self):
        annual_yield = V.implied_annual_yield()
        self.assertTrue(0.02 < annual_yield < 0.25, f"Implied yield {annual_yield:.4f} is implausible.")

    def test_capital_value_and_monthly_income_are_kept_apart(self):
        for engine in (V.SCRAPER_FIXED, V.HYBRID):
            with self.subTest(engine=engine):
                valuation = V.value_property(RENTAL, engine=engine)
                self.assertIsNotNone(valuation.monthly_income)
                self.assertNotAlmostEqual(
                    valuation.capital_value, valuation.monthly_income, places=2,
                    msg="Capital value and monthly income must not be the same number.",
                )

    def test_non_rental_properties_report_no_rental_income(self):
        for prop in (LAND_40, HOUSE):
            with self.subTest(property_type=prop.property_type):
                self.assertIsNone(V.value_property(prop, engine=V.SCRAPER_FIXED).monthly_income)


class HybridEngineTests(unittest.TestCase):
    def test_land_is_valued_by_the_model(self):
        valuation = V.value_property(LAND_40, engine=V.HYBRID)
        self.assertEqual(valuation.method, "model_land")
        self.assertGreater(valuation.capital_value, 0)

    def test_land_without_a_recorded_size_falls_back_and_says_so(self):
        sizeless = Prop(9, "land", "Colombo", 1_000_000, land=Land(land_size=0))
        valuation = V.value_property(sizeless, engine=V.HYBRID)
        self.assertTrue(any("not recorded" in note for note in valuation.notes))

    def test_housing_falls_back_because_the_schema_lacks_bedrooms(self):
        """
        HousingProperty stores no bedrooms or bathrooms, which the house model
        requires. Falling back is correct; inventing them would not be.
        """
        valuation = V.value_property(HOUSE, engine=V.HYBRID)
        self.assertTrue(
            any("bedrooms" in note for note in valuation.notes),
            f"Expected an explanation of the fallback, got {valuation.notes}",
        )

    def test_a_recorded_rent_is_preferred_over_a_model_estimate(self):
        valuation = V.value_property(RENTAL, engine=V.HYBRID)
        self.assertEqual(valuation.method, "stored_rent_capitalised")

    def test_valuation_never_raises(self):
        broken = Prop(99, "land", None, 0, land=None)
        valuation = V.value_property(broken, engine=V.HYBRID)
        self.assertIsInstance(valuation, V.PropertyValuation)

    def test_every_valuation_reports_its_method_and_confidence(self):
        for engine in V.ENGINES:
            for prop in (LAND_40, HOUSE, RENTAL):
                with self.subTest(engine=engine, property_type=prop.property_type):
                    valuation = V.value_property(prop, engine=engine)
                    self.assertTrue(valuation.method)
                    self.assertIn(valuation.confidence, ("high", "medium", "low"))
                    self.assertIn("valuation_method", valuation.as_dict())


class EngineAttributionTests(unittest.TestCase):
    def test_the_middle_engine_separates_the_unit_fix_from_the_model_change(self):
        """
        Without scraper_fixed there is no way to tell whether a change came from
        correcting the units or from switching models.
        """
        portfolio = [LAND_40, LAND_10, HOUSE, RENTAL]
        totals = {
            engine: sum(V.value_property(p, engine=engine).capital_value or 0 for p in portfolio)
            for engine in V.ENGINES
        }
        self.assertGreater(totals[V.SCRAPER_FIXED], totals[V.LEGACY],
                           "Correcting the units must raise the total; land and rent were understated.")
        self.assertNotAlmostEqual(totals[V.HYBRID], totals[V.SCRAPER_FIXED], places=2)


if __name__ == "__main__":
    unittest.main()

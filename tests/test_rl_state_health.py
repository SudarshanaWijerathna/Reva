"""
Tests for RL state distribution health and the portfolio -> RL coupling.

The RL state takes exactly one figure from the portfolio: held-property counts,
in the ``units_owned`` slots. Current value, cost basis and profit reach the agent
through nothing, and these tests pin that down so a future portfolio change does
not quietly acquire a path into the agent.
"""

import unittest
from dataclasses import dataclass, field

from backend.rl import state_health as sh


def state_vector(land: int, rental: int, housing: int, cash: float = 1.0) -> list[float]:
    """A state vector with healthy signals, varying only the counts."""
    signals = (-0.003, 0.0077, 0.0513)
    vector: list[float] = []
    for count in (land, rental, housing):  # PROPERTY_ORDER
        vector.extend([float(count), 0.05, 0.01, 0.15, 0.0, *signals])
    vector.append(cash)
    return vector


class LayoutTests(unittest.TestCase):
    def test_feature_names_match_the_documented_layout(self):
        self.assertEqual(sh.feature_name(0), "land.units_owned")
        self.assertEqual(sh.feature_name(8), "rental.units_owned")
        self.assertEqual(sh.feature_name(16), "housing.units_owned")
        self.assertEqual(sh.feature_name(7), "land.housing_signal")
        self.assertEqual(sh.feature_name(24), "cash_normalised")

    def test_state_size_matches_the_scaler(self):
        self.assertEqual(len(state_vector(1, 1, 1)), int(sh._scaler().n_features_in_))

    def test_a_wrong_length_vector_is_reported_not_scored(self):
        verdict = sh.assess([0.0] * 20)
        self.assertFalse(verdict["in_distribution"])
        self.assertIsNone(verdict["max_abs_z"])
        self.assertTrue(any("scaler expects" in note for note in verdict["notes"]))


class DistributionTests(unittest.TestCase):
    def test_a_small_portfolio_is_in_distribution(self):
        for counts in ((0, 0, 0), (1, 0, 0), (2, 1, 1)):
            with self.subTest(counts=counts):
                self.assertTrue(sh.assess(state_vector(*counts))["in_distribution"])

    def test_a_multi_rental_portfolio_is_flagged(self):
        """
        The training environment rarely held more than one rental, so the scale on
        that feature is 0.47. Three rentals is past +5 sigma.
        """
        verdict = sh.assess(state_vector(1, 3, 1))
        self.assertFalse(verdict["in_distribution"])
        self.assertEqual(verdict["out_of_distribution"][0]["feature"], "rental.units_owned")

    def test_the_flag_names_the_feature_and_its_value(self):
        offender = sh.assess(state_vector(1, 3, 1))["out_of_distribution"][0]
        self.assertEqual(offender["value"], 3.0)
        self.assertEqual(offender["index"], 8)
        self.assertGreater(abs(offender["z"]), 3.0)

    def test_supported_counts_are_reported_for_product_decisions(self):
        bounds = sh.describe_bounds()
        self.assertEqual(set(bounds), {"land", "rental", "housing"})
        for asset, detail in bounds.items():
            with self.subTest(asset=asset):
                self.assertGreaterEqual(detail["max_supported_count"], 0)
        # Land tolerates far more than the other two; this asymmetry is the point.
        self.assertGreater(bounds["land"]["max_supported_count"], bounds["rental"]["max_supported_count"])

    def test_assess_never_alters_the_state(self):
        """Reporting, not clipping: two portfolios must stay distinguishable."""
        original = state_vector(8, 5, 6)
        copy = list(original)
        sh.assess(original)
        self.assertEqual(original, copy)

    def test_cash_slot_stays_in_range_at_its_hardcoded_value(self):
        verdict = sh.assess(state_vector(1, 0, 0, cash=1.0))
        offenders = [item["feature"] for item in verdict["out_of_distribution"]]
        self.assertNotIn("cash_normalised", offenders)

    def test_naively_wiring_cash_to_a_portfolio_ratio_would_break_it(self):
        """
        Training used uninvested cash over initial investment, mean 0.44 - an agent
        that had spent most of its money. A portfolio-value-over-cost-basis ratio
        runs above 1 and lands outside the trained range, so the obvious wiring is
        a trap rather than an improvement.
        """
        verdict = sh.assess(state_vector(1, 0, 0, cash=2.0))
        offenders = [item["feature"] for item in verdict["out_of_distribution"]]
        self.assertIn("cash_normalised", offenders)


# --- portfolio -> RL coupling ------------------------------------------------

@dataclass
class FakeProp:
    id: int
    property_type: str
    status: str = "Active"
    sale_price: float | None = None


@dataclass
class FakeQuery:
    rows: list
    _filtered: bool = False

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows


@dataclass
class FakeDB:
    properties: list = field(default_factory=list)
    sold_transaction_ids: list = field(default_factory=list)

    def query(self, *entities):
        entity = entities[0]
        name = getattr(entity, "__name__", str(entity))
        if "PropertyTransaction" in name or "property_id" in str(entity):
            return FakeQuery([(pid,) for pid in self.sold_transaction_ids])
        return FakeQuery(self.properties)


class PropertyCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.portfolio.service import get_property_counts

        cls.count = staticmethod(get_property_counts)

    def test_held_properties_are_counted_by_type(self):
        db = FakeDB(properties=[
            FakeProp(1, "land"), FakeProp(2, "land"),
            FakeProp(3, "housing"), FakeProp(4, "rental"),
        ])
        self.assertEqual(self.count(db, 1), {"housing": 1, "rental": 1, "land": 2})

    def test_a_sold_property_is_not_held(self):
        db = FakeDB(properties=[
            FakeProp(1, "land"),
            FakeProp(2, "land", sale_price=9_000_000),
            FakeProp(3, "housing", status="Sold"),
        ])
        self.assertEqual(self.count(db, 1), {"housing": 0, "rental": 0, "land": 1})

    def test_a_sale_recorded_only_in_the_ledger_still_counts_as_sold(self):
        db = FakeDB(properties=[FakeProp(1, "land"), FakeProp(2, "land")],
                    sold_transaction_ids=[2])
        self.assertEqual(self.count(db, 1)["land"], 1)

    def test_an_empty_portfolio_returns_zeros_not_an_error(self):
        self.assertEqual(self.count(FakeDB(), 1), {"housing": 0, "rental": 0, "land": 0})

    def test_an_unknown_property_type_is_ignored(self):
        db = FakeDB(properties=[FakeProp(1, "commercial"), FakeProp(2, "land")])
        self.assertEqual(self.count(db, 1), {"housing": 0, "rental": 0, "land": 1})


class CouplingTests(unittest.TestCase):
    def test_the_state_builder_reads_counts_and_not_the_full_portfolio(self):
        """
        Guards the wiring: running the whole portfolio here would pull valuations
        and ledgers into every recommendation, and any failure would return zero
        counts - which the agent cannot tell apart from an empty portfolio.
        """
        import inspect

        from backend.rl import recommendation_api

        source = inspect.getsource(recommendation_api.create_state_vector)
        self.assertIn("get_property_counts", source)
        self.assertNotIn("calculate_portfolio", source)

    def test_no_money_figure_reaches_the_state_vector(self):
        """
        Current value, cost basis and profit must have no path into the agent.
        Comments are stripped first, so documenting the rule does not violate it.
        """
        import inspect
        import io
        import tokenize

        from backend.rl import recommendation_api

        source = inspect.getsource(recommendation_api.create_state_vector)
        code = "".join(
            token.string if token.type not in (tokenize.COMMENT, tokenize.STRING) else " "
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
        )
        for money in ("portfolio_value", "current_value", "profit", "cost_basis", "unrealized"):
            with self.subTest(field=money):
                self.assertNotIn(money, code)


if __name__ == "__main__":
    unittest.main()

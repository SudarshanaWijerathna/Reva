"""
Tests for the property write path.

Two bugs here shared a signature that makes them unusually expensive: the
request returns HTTP 200, the UI says "saved successfully", and the value is
gone. Nothing raises, nothing logs, and the only visible symptom appears on a
different screen as a "-" in the estimated value column. These tests pin both
mechanisms so neither can come back quietly.
"""

import datetime
import unittest

from backend.database.schemas import Property
from backend.properties.models import LandCreate, LandUpdate
from backend.properties.service import SHARED_FIELDS, _copy_fields


def land_body(**overrides):
    """A land payload shaped like the one AddPropertyModal actually sends."""
    body = {
        "location": "imbulgoda",
        "district": "Gampaha",
        "purchase_price": 1_200_000.0,
        "purchase_date": datetime.date(2024, 12, 12),
        "land_size": 10.0,
        "zoning_type": "residential",
        "road_access": "main",
    }
    body.update(overrides)
    return body


class MappedColumnTests(unittest.TestCase):
    def test_every_shared_field_is_a_real_column(self):
        """
        The guard that makes this test possible: assigning an unmapped attribute
        on an ORM instance succeeds and is discarded at flush, so a field the
        model has not caught up with vanishes with no error anywhere.
        """
        _copy_fields(Property(), LandCreate(**land_body()), SHARED_FIELDS)

    def test_an_unmapped_field_raises_instead_of_vanishing(self):
        with self.assertRaises(RuntimeError) as caught:
            _copy_fields(Property(), LandCreate(**land_body()), ("district", "not_a_column"))
        self.assertIn("not_a_column", str(caught.exception))

    def test_the_error_names_every_offending_column(self):
        with self.assertRaises(RuntimeError) as caught:
            _copy_fields(Property(), LandCreate(**land_body()), ("ghost_a", "ghost_b"))
        message = str(caught.exception)
        self.assertIn("ghost_a", message)
        self.assertIn("ghost_b", message)


class CreateTests(unittest.TestCase):
    def test_district_reaches_the_row(self):
        prop = Property()
        _copy_fields(prop, LandCreate(**land_body()), SHARED_FIELDS)
        self.assertEqual(prop.district, "Gampaha")

    def test_a_field_the_client_omitted_is_null_on_create(self):
        prop = Property()
        _copy_fields(prop, LandCreate(**land_body()), SHARED_FIELDS)
        self.assertIsNone(prop.locality)


class UpdateTests(unittest.TestCase):
    """
    The land, housing and rental payloads built by the frontend contain no
    ``locality``, ``latitude`` or ``longitude``. Pydantic supplies None for each,
    so before ``preserve_unsent`` every edit erased any stored geocode - which is
    a silent downgrade of the valuation, not a visible failure.
    """

    def stored_property(self):
        prop = Property()
        prop.location = "imbulgoda"
        prop.district = "Gampaha"
        prop.locality = "Kadawatha"
        prop.latitude = 7.0167
        prop.longitude = 79.9833
        return prop

    def test_an_unsent_field_keeps_its_stored_value(self):
        prop = self.stored_property()
        _copy_fields(prop, LandUpdate(**land_body()), SHARED_FIELDS, preserve_unsent=True)
        self.assertEqual(prop.locality, "Kadawatha")
        self.assertAlmostEqual(prop.latitude, 7.0167)
        self.assertAlmostEqual(prop.longitude, 79.9833)

    def test_a_sent_field_still_overwrites(self):
        prop = self.stored_property()
        body = LandUpdate(**land_body(district="Colombo", locality="Nugegoda"))
        _copy_fields(prop, body, SHARED_FIELDS, preserve_unsent=True)
        self.assertEqual(prop.district, "Colombo")
        self.assertEqual(prop.locality, "Nugegoda")

    def test_an_explicit_null_still_clears_the_value(self):
        """Omitted and explicitly-null must stay distinguishable."""
        prop = self.stored_property()
        body = LandUpdate(**land_body(locality=None))
        _copy_fields(prop, body, SHARED_FIELDS, preserve_unsent=True)
        self.assertIsNone(prop.locality)

    def test_preserve_unsent_off_is_the_old_destructive_behaviour(self):
        """Documents why the create path and the update path differ."""
        prop = self.stored_property()
        _copy_fields(prop, LandUpdate(**land_body()), SHARED_FIELDS)
        self.assertIsNone(prop.locality)


class ValuationBlockerTests(unittest.TestCase):
    def test_a_property_without_a_district_cannot_be_valued(self):
        """The exact condition behind a '-' in the estimated value column."""
        from backend.portfolio.payloads import build_land_payload

        class Detail:
            land_size = 10.0
            road_access = "main"
            electricity = water = clear_deed = bank_loan = near_town = None
            distance_to_town_m = None

        class Prop:
            land = Detail()
            district = None
            location = "imbulgoda"   # not itself a district name
            locality = None

        build = build_land_payload(Prop())
        self.assertIsNone(build.payload)
        self.assertIn("district", build.missing)

    def test_unknown_optional_attributes_do_not_count_as_missing(self):
        """
        They have defined model behaviour when absent. Counting them as missing
        marked a fully specified plot incomplete and dropped its confidence to
        low for not recording whether it has mains water.
        """
        from backend.portfolio.payloads import build_land_payload

        class Detail:
            land_size = 10.0
            road_access = "main"
            electricity = water = clear_deed = bank_loan = near_town = None
            distance_to_town_m = None

        class Prop:
            land = Detail()
            district = "Gampaha"
            location = "imbulgoda"
            locality = "imbulgoda"

        build = build_land_payload(Prop())
        self.assertIsNotNone(build.payload)
        self.assertEqual(build.missing, [])
        self.assertTrue(build.complete)
        self.assertTrue(any("Unknown optional" in note for note in build.notes))


if __name__ == "__main__":
    unittest.main()

import csv
import shutil
import unittest
from pathlib import Path

from scripts.preprocess_rental_data import (
    add_quality_flags,
    base_record,
    build_feature_records,
    normalize_property_type,
    parse_money_lkr,
    parse_months,
    parse_number,
    preprocess,
    safe_parse_properties,
)


class RentalParserTests(unittest.TestCase):
    def test_parse_money_lkr_handles_rupee_and_embedded_usd(self):
        self.assertEqual(parse_money_lkr("Rs 700,000 /month"), 700000.0)
        self.assertEqual(parse_money_lkr("Rs. 325,000($ 1,110)"), 325000.0)
        self.assertEqual(parse_money_lkr("185000"), 185000.0)
        self.assertIsNone(parse_money_lkr("N/A"))

    def test_parse_number_handles_units_and_commas(self):
        self.assertEqual(parse_number("1,600 sqft"), 1600.0)
        self.assertEqual(parse_number("47.0 perches"), 47.0)
        self.assertIsNone(parse_number("N/A"))

    def test_parse_months_converts_years(self):
        self.assertEqual(parse_months("3 Months"), 3.0)
        self.assertEqual(parse_months("2 Years"), 24.0)
        self.assertIsNone(parse_months("N/A"))

    def test_safe_parse_properties(self):
        parsed = safe_parse_properties("{'Beds': '3', 'Baths': '2', 'Size': '1,100 sqft'}")
        self.assertEqual(parsed["Beds"], "3")
        self.assertEqual(parsed["Size"], "1,100 sqft")
        self.assertEqual(safe_parse_properties("not a dict"), {})

    def test_normalize_property_type_aliases(self):
        self.assertEqual(normalize_property_type("Annexe"), "Annex")
        self.assertEqual(normalize_property_type("Warehouse / Storage"), "Warehouse")
        self.assertEqual(normalize_property_type("", "Apartment Rentals"), "Apartment")
        self.assertEqual(normalize_property_type("Office", "Commercial Property Rentals"), "Office space")


class RentalQualityTests(unittest.TestCase):
    def test_quality_flags_exclude_bad_prices_and_duplicates(self):
        good = base_record(
            source="test",
            source_file="sample.csv",
            listing_id="a",
            listing_url="",
            title="Nice apartment",
            property_type="Apartment",
            location="Colombo 5",
            district="Colombo",
            monthly_rent_lkr=150000,
            bedrooms=2,
            bathrooms=2,
            floor_area_sqft=1000,
            furnishing_status="furnished",
        )
        duplicate = dict(good)
        duplicate["record_id"] = "different"
        duplicate["_raw_fingerprint"] = "same"
        good["_raw_fingerprint"] = "same"
        impossible = base_record(
            source="test",
            source_file="sample.csv",
            listing_id="b",
            title="Broken listing",
            property_type="Apartment",
            location="Colombo 5",
            district="Colombo",
            monthly_rent_lkr=750000000,
            bedrooms=2,
            bathrooms=2,
            floor_area_sqft=1000,
            furnishing_status="unknown",
        )

        records = [good, duplicate, impossible]
        add_quality_flags(records)

        self.assertEqual(records[0]["is_training_excluded"], 0)
        self.assertEqual(records[1]["flag_duplicate_exact"], 1)
        self.assertIn("duplicate_exact", records[1]["exclusion_reason"])
        self.assertEqual(records[2]["flag_impossible_price"], 1)
        self.assertIn("impossible_price", records[2]["exclusion_reason"])

        features = build_feature_records(records)
        self.assertEqual(len(features), 1)
        self.assertGreater(features[0]["log_monthly_rent_lkr"], 0)


class RentalPreprocessSmokeTests(unittest.TestCase):
    def test_preprocess_writes_cleaned_features_and_report(self):
        root = Path.cwd() / "tests" / "_tmp_rental_preprocessing"
        shutil.rmtree(root, ignore_errors=True)
        try:
            input_dir = root / "input"
            input_dir.mkdir(parents=True, exist_ok=True)
            self._write_required_inputs(input_dir)

            processed = root / "processed.csv"
            features = root / "features.csv"
            report = root / "report.json"
            summary = preprocess(input_dir, processed, features, report)

            self.assertTrue(processed.exists())
            self.assertTrue(features.exists())
            self.assertTrue(report.exists())
            self.assertGreater(summary["cleaned_rows"], 0)
            self.assertGreater(summary["feature_rows"], 0)

            with features.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertTrue(all(float(row["monthly_rent_lkr"]) > 0 for row in rows))
            self.assertEqual(len(rows), len({tuple(row.items()) for row in rows}))
            self.assertIn("property_type", rows[0])
            self.assertIn("amenity_swimming_pool", rows[0])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def _write_required_inputs(self, input_dir: Path) -> None:
        category_header = [
            "ad_title",
            "ad_description",
            "details",
            "slug",
            "title",
            "type",
            "price",
            "timestamp",
            "posted_date",
            "deactivation_date",
            "category",
            "parent_category",
            "location",
            "geo_region",
            "area",
            "is_delivery_free",
            "is_doorstep_delivery",
            "is_dsd_applicable",
            "is_member",
            "is_authorized_dealer",
            "is_featured_member",
            "is_verified",
            "membership_level",
            "member_since",
            "properties",
            "user",
        ]
        rows_by_file = {
            "apartment_rentals_properties.csv": [
                self._category_row(category_header, "Apartment Rentals", "apt-1", "Rs 150,000 /month")
            ],
            "house_rentals_properties.csv": [
                self._category_row(category_header, "House Rentals", "house-1", "Rs 95,000 /month")
            ],
            "commercial_property_rentals_properties.csv": [
                self._category_row(
                    category_header,
                    "Commercial Property Rentals",
                    "office-1",
                    "Rs 250,000 /month",
                    "{'Property type': 'Office', 'Size': '1,200 sqft'}",
                )
            ],
            "room_&_annex_rentals_properties.csv": [
                self._category_row(
                    category_header,
                    "Room & Annex Rentals",
                    "annex-1",
                    "Rs 20,000 /month",
                    "{'Property type': 'Annex', 'Beds': '1', 'Baths': '1'}",
                )
            ],
        }
        for file_name, rows in rows_by_file.items():
            self._write_csv(input_dir / file_name, category_header, rows)

        self._write_csv(
            input_dir / "ikman_rentals_2026.csv",
            [
                "source",
                "listing_url",
                "title",
                "price_lkr",
                "address",
                "bedrooms",
                "bathrooms",
                "house_sqft",
                "land_perches",
                "posted_on_text",
                "sublocation",
                "district",
                "description_raw",
            ],
            [
                {
                    "source": "ikman.lk",
                    "listing_url": "https://example.test/rent-1",
                    "title": "House for rent",
                    "price_lkr": "85000",
                    "address": "Malabe, Colombo",
                    "bedrooms": "3",
                    "bathrooms": "2",
                    "house_sqft": "1400",
                    "land_perches": "8",
                    "posted_on_text": "Posted on 07 May 8:54 am",
                    "sublocation": "Malabe",
                    "district": "Colombo",
                    "description_raw": "Brand new house with parking",
                }
            ],
        )
        self._write_csv(
            input_dir / "rental_details_lankapropertyweb.csv",
            [
                "URL",
                "Title",
                "Location",
                "Price_Per_Month",
                "Property Type",
                "Bedrooms",
                "Bathrooms/WCs",
                "Floor area",
                "Floor Number",
                "Deposit",
                "Min. lease term",
                "Availability",
                "Price per sq.ft.",
                "Car parking spaces",
                "Furnishing Status",
                "Advance payment",
                "Short term",
                "Description",
                "Features",
            ],
            [
                {
                    "URL": "https://example.test/lpw-1",
                    "Title": "Luxury apartment",
                    "Location": "Colombo 3",
                    "Price_Per_Month": "Rs. 325,000($ 1,110)",
                    "Property Type": "Apartment",
                    "Bedrooms": "2",
                    "Bathrooms/WCs": "2",
                    "Floor area": "1,100 sqft",
                    "Floor Number": "4",
                    "Deposit": "3 Months",
                    "Min. lease term": "1 Years",
                    "Availability": "Available",
                    "Price per sq.ft.": "Rs. 290 Per Month",
                    "Car parking spaces": "1",
                    "Furnishing Status": "Furnished",
                    "Advance payment": "3 Months",
                    "Short term": "No",
                    "Description": "Apartment with pool and security",
                    "Features": "SWIMMING POOL, 24 HOUR SECURITY",
                }
            ],
        )

    def _category_row(
        self,
        header,
        category,
        slug,
        price,
        properties="{'Beds': '2', 'Baths': '1', 'Size': '900 sqft'}",
    ):
        row = {column: "" for column in header}
        row.update(
            {
                "ad_title": slug,
                "ad_description": "Clean property with parking",
                "slug": slug,
                "title": slug,
                "type": "for_rent",
                "price": price,
                "posted_date": "07 May",
                "category": category,
                "parent_category": "Property",
                "location": "Colombo 5",
                "area": "{'id': 1506, 'name': 'Colombo'}",
                "properties": properties,
            }
        )
        return row

    def _write_csv(self, path, header, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

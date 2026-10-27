import tempfile
import unittest
from pathlib import Path

from simulation import (
    add_catalog_brand,
    build_equipment_maps,
    create_sample_chain,
    load_company_equipment,
    parse_equipment_types,
    remove_catalog_brand,
    save_company_equipment,
    update_catalog_brand,
    validate_company_equipment,
)


class EquipmentCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {"Northstar": ["Excavators", "Wheel Loaders"]}

    def test_add_edit_and_remove_brands(self):
        added = add_catalog_brand(self.catalog, "Atlas Works", ["Cranes"])
        edited = update_catalog_brand(
            added, "Atlas Works", "Atlas Equipment", ["Cranes", "Hoists"]
        )
        removed = remove_catalog_brand(edited, "Northstar")

        self.assertEqual(
            removed,
            {"Atlas Equipment": ["Cranes", "Hoists"]},
        )

    def test_duplicate_names_and_invalid_equipment_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            add_catalog_brand(self.catalog, "northstar", ["Dozers"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            update_catalog_brand(
                add_catalog_brand(self.catalog, "Atlas Works", ["Cranes"]),
                "Northstar",
                "atlas works",
                ["Dozers"],
            )
        with self.assertRaisesRegex(ValueError, "Duplicate equipment type"):
            add_catalog_brand(self.catalog, "Atlas", ["Cranes", " cranes "])
        with self.assertRaisesRegex(ValueError, "inconsistent spelling"):
            validate_company_equipment(
                {"Northstar": ["Excavators"], "Atlas": ["excavators"]}
            )
        with self.assertRaisesRegex(ValueError, "at least one equipment type"):
            add_catalog_brand(self.catalog, "Atlas", [])

    def test_catalog_cannot_remove_its_last_brand(self):
        with self.assertRaisesRegex(ValueError, "at least one brand"):
            remove_catalog_brand({"Northstar": ["Excavators"]}, "Northstar")

    def test_catalog_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            saved = save_company_equipment(
                {"Northstar": ["Excavators"], "Atlas": ["Cranes"]}, path
            )
            self.assertEqual(load_company_equipment(path), saved)

    def test_scenario_maps_are_built_from_the_supplied_catalog(self):
        custom_catalog = {"Atlas Works": ["Crawler Cranes"]}
        categories, suppliers, manufacturers = build_equipment_maps(custom_catalog)
        simulation = create_sample_chain(
            num_suppliers=1,
            num_manufacturers=1,
            num_customers=1,
            company_equipment=custom_catalog,
        )

        self.assertEqual(categories["Crawler Cranes"]["manufacturers"], ["Atlas Works"])
        self.assertEqual(suppliers["Crawler Cranes"], ["Atlas Works (Crawler Cranes)"])
        self.assertEqual(
            manufacturers["Crawler Cranes"], ["Atlas Works (Crawler Cranes)"]
        )
        self.assertEqual(
            simulation.equipment_categories["Crawler Cranes"]["suppliers"],
            ["Atlas Works"],
        )
        self.assertEqual(simulation.suppliers[0].category, "Crawler Cranes")
        self.assertEqual(simulation.manufacturers[0].category, "Crawler Cranes")

    def test_type_parser_accepts_lines_and_commas(self):
        self.assertEqual(
            parse_equipment_types("Excavators, Cranes\nWheel Loaders"),
            ["Excavators", "Cranes", "Wheel Loaders"],
        )

    def test_workspace_catalog_is_seeded_with_existing_market_data(self):
        catalog = load_company_equipment()
        self.assertIn("Caterpillar", catalog)
        self.assertIn("Excavators", catalog["Caterpillar"])
        self.assertGreaterEqual(len(catalog), 1)


if __name__ == "__main__":
    unittest.main()

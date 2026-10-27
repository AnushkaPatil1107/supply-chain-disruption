import unittest

from simulation import calculate_customer_order_impact, create_sample_chain


class CustomerOrderImpactTests(unittest.TestCase):
    def test_order_coverage_counts_only_selected_equipment_and_brand(self):
        results = {
            "manufacturer_production": {
                "Caterpillar (Excavators)": 70,
                "Komatsu (Excavators)": 20,
                "Caterpillar (Bulldozers)": 500,
            }
        }

        impact = calculate_customer_order_impact(
            results,
            equipment_type="Excavators",
            order_quantity=100,
            on_hand_units=10,
            brand="Caterpillar",
        )

        self.assertEqual(impact["available_units"], 70)
        self.assertEqual(impact["units_from_supply"], 70)
        self.assertEqual(impact["inventory_used"], 10)
        self.assertEqual(impact["covered_units"], 80)
        self.assertEqual(impact["uncovered_units"], 20)
        self.assertEqual(impact["coverage_percentage"], 80)

    def test_flexible_brand_order_can_use_any_listed_equivalent(self):
        results = {
            "manufacturer_production": {
                "Caterpillar (Excavators)": 70,
                "Komatsu (Excavators)": 20,
                "Caterpillar (Bulldozers)": 500,
            }
        }

        impact = calculate_customer_order_impact(
            results, "Excavators", order_quantity=100, on_hand_units=0
        )

        self.assertEqual(impact["available_units"], 90)
        self.assertEqual(impact["uncovered_units"], 10)
        self.assertEqual(impact["coverage_percentage"], 90)

    def test_targeted_simulation_uses_only_the_ordered_equipment_and_brand(self):
        catalog = {
            "Northstar": ["Excavators", "Dozers"],
            "Atlas Works": ["Excavators"],
            "Roadworks": ["Dozers"],
        }
        simulation = create_sample_chain(
            num_suppliers=2,
            num_manufacturers=2,
            num_customers=1,
            company_equipment=catalog,
            target_equipment_type="Excavators",
            target_brand="Northstar",
        )

        self.assertEqual(
            {supplier.category for supplier in simulation.suppliers}, {"Excavators"}
        )
        self.assertIn(
            "Northstar (Excavators)",
            {supplier.display_name for supplier in simulation.suppliers},
        )
        self.assertEqual(len(simulation.manufacturers), 1)
        self.assertEqual(simulation.manufacturers[0].display_name, "Northstar (Excavators)")

    def test_recovery_only_restores_production_when_a_solution_has_an_alternative(self):
        catalog = {"Northstar": ["Excavators"], "Atlas Works": ["Excavators"]}
        simulation = create_sample_chain(
            num_suppliers=2,
            num_manufacturers=1,
            num_customers=1,
            company_equipment=catalog,
            target_equipment_type="Excavators",
            target_brand="Northstar",
            disruption_probability=0,
        )
        simulation.units_produced["Northstar (Excavators)_Excavators"] = 100
        simulation.disruptions["Northstar (Excavators)"] = "Supply chain delay"
        simulation.solutions["Northstar (Excavators)"] = "No solution available"

        disrupted = simulation.simulate_with_disruptions()
        recovered = simulation.simulate_with_solutions()

        self.assertEqual(disrupted["manufacturer_production"]["Northstar (Excavators)"], 30)
        self.assertEqual(recovered["manufacturer_production"]["Northstar (Excavators)"], 30)

        simulation.solutions["Northstar (Excavators)"] = "Source from alternative supplier"
        recovered = simulation.simulate_with_solutions()
        self.assertEqual(recovered["manufacturer_production"]["Northstar (Excavators)"], 100)

    def test_invalid_customer_order_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            calculate_customer_order_impact({}, "Excavators", 0)
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            calculate_customer_order_impact({}, "Excavators", 1, -1)


if __name__ == "__main__":
    unittest.main()

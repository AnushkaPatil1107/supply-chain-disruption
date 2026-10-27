import random
import json
import os
import re
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, NamedTuple
from faker import Faker

fake = Faker()

CATALOG_FILE = Path(__file__).with_name("equipment_catalog.json")


def validate_company_equipment(company_equipment: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Validate and normalize an equipment catalog before it is used or saved."""
    if not isinstance(company_equipment, dict) or not company_equipment:
        raise ValueError("The catalog must contain at least one brand.")

    normalized_catalog = {}
    seen_brands = set()
    canonical_types = {}

    for raw_brand, raw_types in company_equipment.items():
        if not isinstance(raw_brand, str):
            raise ValueError("Every brand name must be text.")
        brand = raw_brand.strip()
        if not brand:
            raise ValueError("Brand names cannot be blank.")
        if len(brand) > 100:
            raise ValueError(f"Brand name '{brand[:30]}…' is too long (maximum 100 characters).")
        brand_key = brand.casefold()
        if brand_key in seen_brands:
            raise ValueError(f"Duplicate brand name: '{brand}'.")
        seen_brands.add(brand_key)

        if not isinstance(raw_types, (list, tuple)) or not raw_types:
            raise ValueError(f"Brand '{brand}' must have at least one equipment type.")

        normalized_types = []
        seen_types_for_brand = set()
        for raw_type in raw_types:
            if not isinstance(raw_type, str):
                raise ValueError(f"Equipment types for '{brand}' must be text.")
            equipment_type = raw_type.strip()
            if not equipment_type:
                raise ValueError(f"Brand '{brand}' has a blank equipment type.")
            if len(equipment_type) > 100:
                raise ValueError(
                    f"Equipment type '{equipment_type[:30]}…' is too long (maximum 100 characters)."
                )
            type_key = equipment_type.casefold()
            if type_key in seen_types_for_brand:
                raise ValueError(
                    f"Duplicate equipment type '{equipment_type}' for brand '{brand}'."
                )
            seen_types_for_brand.add(type_key)

            canonical_type = canonical_types.get(type_key)
            if canonical_type is not None and canonical_type != equipment_type:
                raise ValueError(
                    f"Equipment type '{equipment_type}' has inconsistent spelling. "
                    f"Use '{canonical_type}' everywhere."
                )
            canonical_types.setdefault(type_key, equipment_type)
            normalized_types.append(canonical_types[type_key])

        normalized_catalog[brand] = normalized_types

    return normalized_catalog


def parse_equipment_types(raw_types: str) -> List[str]:
    """Parse the catalog editor's comma- or line-separated equipment list."""
    if not isinstance(raw_types, str):
        raise ValueError("Equipment types must be entered as text.")
    return [part.strip() for part in re.split(r"[,\n]", raw_types) if part.strip()]


def add_catalog_brand(
    company_equipment: Dict[str, List[str]], brand_name: str, equipment_types: List[str]
) -> Dict[str, List[str]]:
    catalog = validate_company_equipment(company_equipment)
    normalized_brand = brand_name.strip() if isinstance(brand_name, str) else ""
    if any(brand.casefold() == normalized_brand.casefold() for brand in catalog):
        raise ValueError(f"Brand '{normalized_brand}' already exists.")
    catalog[normalized_brand] = equipment_types
    return validate_company_equipment(catalog)


def update_catalog_brand(
    company_equipment: Dict[str, List[str]],
    current_brand: str,
    new_brand: str,
    equipment_types: List[str],
) -> Dict[str, List[str]]:
    catalog = validate_company_equipment(company_equipment)
    if current_brand not in catalog:
        raise ValueError(f"Brand '{current_brand}' no longer exists.")
    normalized_brand = new_brand.strip() if isinstance(new_brand, str) else ""
    if any(
        brand != current_brand and brand.casefold() == normalized_brand.casefold()
        for brand in catalog
    ):
        raise ValueError(f"Brand '{normalized_brand}' already exists.")

    updated_catalog = {
        normalized_brand if brand == current_brand else brand:
        (equipment_types if brand == current_brand else types)
        for brand, types in catalog.items()
    }
    return validate_company_equipment(updated_catalog)


def remove_catalog_brand(
    company_equipment: Dict[str, List[str]], brand_name: str
) -> Dict[str, List[str]]:
    catalog = validate_company_equipment(company_equipment)
    if brand_name not in catalog:
        raise ValueError(f"Brand '{brand_name}' no longer exists.")
    if len(catalog) == 1:
        raise ValueError("The catalog must keep at least one brand.")
    del catalog[brand_name]
    return validate_company_equipment(catalog)


def load_company_equipment(path: Path = CATALOG_FILE) -> Dict[str, List[str]]:
    """Load and validate the workspace's editable equipment catalog."""
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise FileNotFoundError(f"Equipment catalog file not found: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as catalog_file:
        saved_catalog = json.load(catalog_file)
    return validate_company_equipment(saved_catalog)


def save_company_equipment(
    company_equipment: Dict[str, List[str]], path: Path = CATALOG_FILE
) -> Dict[str, List[str]]:
    """Validate and atomically persist an equipment catalog."""
    normalized_catalog = validate_company_equipment(company_equipment)
    catalog_path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=catalog_path.parent,
            prefix=f".{catalog_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as catalog_file:
            temporary_path = Path(catalog_file.name)
            json.dump(normalized_catalog, catalog_file, indent=2, ensure_ascii=False)
            catalog_file.write("\n")
        os.replace(temporary_path, catalog_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    if catalog_path.resolve() == CATALOG_FILE.resolve():
        global COMPANY_EQUIPMENT, EQUIPMENT_CATEGORIES, SUPPLIERS, MANUFACTURERS
        COMPANY_EQUIPMENT = normalized_catalog
        EQUIPMENT_CATEGORIES, SUPPLIERS, MANUFACTURERS = build_equipment_maps(
            normalized_catalog
        )

    return normalized_catalog


def build_equipment_maps(company_equipment: Dict[str, List[str]]):
    """Build equipment categories and selectable supply/manufacturer entries."""
    catalog = validate_company_equipment(company_equipment)
    equipment_categories = {}
    for brand, equipment_types in catalog.items():
        for equipment_type in equipment_types:
            category = equipment_categories.setdefault(
                equipment_type, {"suppliers": [], "manufacturers": []}
            )
            category["suppliers"].append(brand)
            category["manufacturers"].append(brand)

    suppliers = {
        category: [f"{brand} ({category})" for brand in details["suppliers"]]
        for category, details in equipment_categories.items()
    }
    manufacturers = {
        category: [f"{brand} ({category})" for brand in details["manufacturers"]]
        for category, details in equipment_categories.items()
    }
    return equipment_categories, suppliers, manufacturers


# Keep these maps available for existing imports; simulations reload the editable
# catalog when no explicit catalog is passed.
COMPANY_EQUIPMENT = load_company_equipment()
EQUIPMENT_CATEGORIES, SUPPLIERS, MANUFACTURERS = build_equipment_maps(COMPANY_EQUIPMENT)


class PresetScenario(NamedTuple):
    name: str
    description: str
    suppliers: int
    manufacturers: int
    base_inventory: int
    disruption_probability: float


PRESETS = [
    PresetScenario(
        name="Normal Operations",
        description="A baseline supply scenario for the selected equipment order",
        suppliers=8,
        manufacturers=5,
        base_inventory=250,
        disruption_probability=0.1
    ),
    PresetScenario(
        name="Critical Parts Shortage",
        description="A component shortage reduces supply available for your equipment order",
        suppliers=8,
        manufacturers=5,
        base_inventory=120,
        disruption_probability=0.7
    ),
    PresetScenario(
        name="Regional Weather Event",
        description="Severe weather slows the modeled supply network for your equipment",
        suppliers=8,
        manufacturers=5,
        base_inventory=180,
        disruption_probability=0.4
    ),
    PresetScenario(
        name="Infrastructure Demand Surge",
        description="Higher project demand leaves less modeled supply for your order",
        suppliers=8,
        manufacturers=5,
        base_inventory=200,
        disruption_probability=0.5
    ),
    PresetScenario(
        name="Freight Bottleneck",
        description="A transport bottleneck reduces supply reaching your project",
        suppliers=8,
        manufacturers=5,
        base_inventory=300,
        disruption_probability=0.3
    ),
]


class SupplyChainNode:
    def __init__(self, name: str, category: str, inventory: int = 100):
        self.name = name
        self.category = category
        self.inventory = inventory
        self.supply_amount = 0

    @property
    def display_name(self) -> str:
        suffix = f" ({self.category})"
        return self.name if self.name.endswith(suffix) else f"{self.name}{suffix}"


class ManufacturerNode:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category

    @property
    def display_name(self) -> str:
        suffix = f" ({self.category})"
        return self.name if self.name.endswith(suffix) else f"{self.name}{suffix}"


class SupplyChainSimulation:
    def __init__(self,
                 num_suppliers: int,
                 num_manufacturers: int,
                 num_customers: int,
                 base_inventory: int = 100,
                 disruption_probability: float = 0.2,
                 company_equipment: Dict[str, List[str]] = None,
                 target_equipment_type: str = None,
                 target_brand: str = None):
        self.disruption_probability = disruption_probability
        self.target_equipment_type = target_equipment_type
        self.target_brand = target_brand
        self.equipment_categories, self.supplier_catalog, self.manufacturer_catalog = (
            build_equipment_maps(
                load_company_equipment() if company_equipment is None else company_equipment
            )
        )

        if target_equipment_type and target_equipment_type not in self.equipment_categories:
            raise ValueError(f"Unknown equipment type: {target_equipment_type}")
        if target_brand and (
            not target_equipment_type
            or target_brand not in self.equipment_categories[target_equipment_type]["manufacturers"]
        ):
            raise ValueError(
                f"Brand '{target_brand}' does not list {target_equipment_type}."
            )

        all_available_suppliers = []
        for category, suppliers_list in self.supplier_catalog.items():
            if target_equipment_type and category != target_equipment_type:
                continue
            for supplier in suppliers_list:
                all_available_suppliers.append((supplier, category))

        if target_equipment_type:
            if not all_available_suppliers:
                raise ValueError(f"No listed suppliers for {target_equipment_type}.")
            num_suppliers = min(num_suppliers, len(all_available_suppliers))

        if num_suppliers <= len(all_available_suppliers):
            preferred_supplier = next(
                (
                    pair for pair in all_available_suppliers
                    if target_brand and pair[0].startswith(f"{target_brand} (")
                ),
                None
            )
            if preferred_supplier and num_suppliers > 0:
                remaining_suppliers = [
                    pair for pair in all_available_suppliers if pair != preferred_supplier
                ]
                selected_suppliers = [preferred_supplier]
                selected_suppliers.extend(
                    random.sample(remaining_suppliers, num_suppliers - 1)
                )
            else:
                selected_suppliers = random.sample(all_available_suppliers, num_suppliers)
        else:
            selected_suppliers = list(all_available_suppliers)
            additional_needed = num_suppliers - len(all_available_suppliers)
            for i in range(additional_needed):
                original_supplier, category = random.choice(all_available_suppliers)
                selected_suppliers.append((f"{original_supplier} (Instance {i+1})", category))

        self.suppliers = [
            SupplyChainNode(name, category, base_inventory)
            for name, category in selected_suppliers
        ]

        all_available_manufacturers = []
        for category, manufacturers_list in self.manufacturer_catalog.items():
            if target_equipment_type and category != target_equipment_type:
                continue
            for manufacturer in manufacturers_list:
                if target_brand and not manufacturer.startswith(f"{target_brand} ("):
                    continue
                all_available_manufacturers.append((manufacturer, category))

        if target_equipment_type:
            if not all_available_manufacturers:
                raise ValueError(
                    f"No listed equipment producer for {target_equipment_type}"
                    + (f" from {target_brand}." if target_brand else ".")
                )
            num_manufacturers = min(num_manufacturers, len(all_available_manufacturers))

        if num_manufacturers <= len(all_available_manufacturers):
            selected_manufacturers = random.sample(all_available_manufacturers, num_manufacturers)
        else:
            selected_manufacturers = list(all_available_manufacturers)
            additional_needed = num_manufacturers - len(all_available_manufacturers)
            for i in range(additional_needed):
                original_manufacturer, category = random.choice(all_available_manufacturers)
                selected_manufacturers.append((f"{original_manufacturer} (Instance {i+1})", category))

        self.manufacturers = [
            ManufacturerNode(name, category)
            for name, category in selected_manufacturers
        ]

        self.customers = [fake.name() for _ in range(num_customers)]
        self.units_produced = {f"{m.name}_{m.category}": 0 for m in self.manufacturers}
        self.disruptions: Dict[str, str] = {}
        self.solutions: Dict[str, str] = {}

    def simulate_normal(self) -> Dict:
        results = {
            'supplier_amounts': {
                s.display_name: s.supply_amount for s in self.suppliers
            },
            'manufacturer_production': {
                m.display_name: self.units_produced[f"{m.name}_{m.category}"]
                for m in self.manufacturers
            },
            'customer_received': sum(self.units_produced.values())
        }
        return results

    def simulate_with_disruptions(self) -> Dict:
        disruption_types = [
            "Supply chain delay",
            "Production facility shutdown",
            "Materials shortage",
            "Transportation issues",
            "Quality control failure",
            "Labor shortage",
            "Natural disaster",
            "Weather-related delays",
            "Customs or import delay",
            "Component shortage"
        ]

        any_manual_disruptions = bool(self.disruptions)

        if not any_manual_disruptions:
            for supplier in self.suppliers:
                if random.random() < self.disruption_probability:
                    disruption = random.choice(disruption_types)
                    self.disruptions[supplier.name] = disruption
                    solutions = [
                        "Source from alternative supplier",
                        "Expedite shipment through premium freight",
                        "Implement temporary production change",
                        "Activate emergency supply contract",
                        "Utilize inventory reserves"
                    ]
                    self.solutions[supplier.name] = random.choice(solutions)

        original_supply = {s.display_name: s.supply_amount for s in self.suppliers}
        disrupted_supply = original_supply.copy()

        for supplier in self.suppliers:
            if supplier.name in self.disruptions:
                reduction_factor = random.uniform(0.2, 0.5)
                disrupted_supply[supplier.display_name] *= reduction_factor

        reduced_production = {}
        for manufacturer in self.manufacturers:
            category = manufacturer.category
            category_suppliers = [s for s in self.suppliers if s.category == category]
            disrupted_category_suppliers = [s for s in category_suppliers if s.name in self.disruptions]

            if category_suppliers:
                if self.target_brand and category == self.target_equipment_type:
                    target_brand_disrupted = any(
                        supplier.name.startswith(f"{self.target_brand} (")
                        for supplier in disrupted_category_suppliers
                    )
                    disruption_ratio = 1.0 if target_brand_disrupted else 0.0
                else:
                    disruption_ratio = (
                        len(disrupted_category_suppliers) / len(category_suppliers)
                    )
                production_factor = max(0.3, 1.0 - (disruption_ratio * 0.7))
            else:
                production_factor = 0.7

            reduced_production[manufacturer.display_name] = int(
                self.units_produced[f"{manufacturer.name}_{manufacturer.category}"] * production_factor
            )

        results = {
            'supplier_amounts': disrupted_supply,
            'manufacturer_production': reduced_production,
            'customer_received': sum(reduced_production.values()),
            'disruption_events': [
                {'supplier': s.name.removesuffix(f" ({s.category})"),
                 'category': s.category,
                 'disruption': self.disruptions[s.name]}
                for s in self.suppliers
                if s.name in self.disruptions
            ]
        }
        return results

    def simulate_with_solutions(self) -> Dict:
        solved_supply = {s.display_name: s.supply_amount for s in self.suppliers}
        recovered_suppliers = set()

        no_solution_phrases = ["not found", "not available", "no solution",
                               "unavailable", "unknown", "none", "n/a", "tbd"]

        for category in self.supplier_catalog:
            category_suppliers = [s for s in self.suppliers if s.category == category]
            working_suppliers = [s for s in category_suppliers if s.name not in self.disruptions]

            for supplier in category_suppliers:
                if supplier.name not in self.disruptions:
                    continue
                solution_text = str(self.solutions.get(supplier.name, "") or "").strip().lower()
                has_solution = (
                    solution_text and
                    not any(phrase in solution_text for phrase in no_solution_phrases) and
                    solution_text not in no_solution_phrases
                )
                if has_solution and working_suppliers:
                    recovered_suppliers.add(supplier.name)
                    extra_load = solved_supply[supplier.display_name] / len(working_suppliers)
                    for ws in working_suppliers:
                        solved_supply[ws.display_name] += extra_load

        solved_production = {}
        for manufacturer in self.manufacturers:
            category_suppliers = [
                supplier for supplier in self.suppliers
                if supplier.category == manufacturer.category
            ]
            if self.target_brand and manufacturer.category == self.target_equipment_type:
                category_suppliers = [
                    supplier for supplier in category_suppliers
                    if supplier.name.startswith(f"{self.target_brand} (")
                ]
            unresolved_suppliers = [
                supplier for supplier in category_suppliers
                if supplier.name in self.disruptions
                and supplier.name not in recovered_suppliers
            ]
            if category_suppliers:
                disruption_ratio = len(unresolved_suppliers) / len(category_suppliers)
                production_factor = max(0.3, 1.0 - (disruption_ratio * 0.7))
            else:
                production_factor = 0.7
            baseline_production = self.units_produced[
                f"{manufacturer.name}_{manufacturer.category}"
            ]
            solved_production[manufacturer.display_name] = int(
                baseline_production * production_factor
            )

        results = {
            'supplier_amounts': solved_supply,
            'manufacturer_production': solved_production,
            'customer_received': sum(solved_production.values()),
            'solution_events': [
                {
                    'disrupted_supplier': s.name,
                    'category': s.category,
                    'solution': self.solutions.get(s.name, "No solution provided"),
                    'redistributed_to': [
                        ws.name for ws in self.suppliers
                        if ws.category == s.category and ws.name not in self.disruptions
                    ]
                }
                for s in self.suppliers
                if s.name in self.disruptions
            ]
        }
        return results


def create_sample_chain(
    num_suppliers: int = 3,
    num_manufacturers: int = 3,
    num_customers: int = 5,
    base_inventory: int = 100,
    disruption_probability: float = 0.2,
    company_equipment: Dict[str, List[str]] = None,
    target_equipment_type: str = None,
    target_brand: str = None
) -> SupplyChainSimulation:
    return SupplyChainSimulation(
        num_suppliers=num_suppliers,
        num_manufacturers=num_manufacturers,
        num_customers=num_customers,
        base_inventory=base_inventory,
        disruption_probability=disruption_probability,
        company_equipment=company_equipment,
        target_equipment_type=target_equipment_type,
        target_brand=target_brand
    )


def calculate_customer_order_impact(
    results: Dict,
    equipment_type: str,
    order_quantity: int,
    on_hand_units: int = 0,
    brand: str = None,
) -> Dict[str, float]:
    """Estimate how much of a buyer's order available supply and stock can cover."""
    if not equipment_type:
        raise ValueError("Select an equipment type for the order.")
    if order_quantity < 1:
        raise ValueError("Order quantity must be at least one unit.")
    if on_hand_units < 0:
        raise ValueError("On-hand inventory cannot be negative.")

    production = results.get("manufacturer_production", {})
    category_suffix = f" ({equipment_type})"
    brand_prefix = f"{brand} (" if brand else None
    available_units = sum(
        max(0, float(units))
        for label, units in production.items()
        if label.endswith(category_suffix)
        and (brand_prefix is None or label.startswith(brand_prefix))
    )
    available_units = int(round(available_units))
    units_from_supply = min(order_quantity, available_units)
    inventory_used = min(on_hand_units, order_quantity - units_from_supply)
    covered_units = units_from_supply + inventory_used
    uncovered_units = max(0, order_quantity - covered_units)

    return {
        "order_quantity": order_quantity,
        "available_units": available_units,
        "units_from_supply": units_from_supply,
        "inventory_used": inventory_used,
        "covered_units": covered_units,
        "uncovered_units": uncovered_units,
        "coverage_percentage": covered_units / order_quantity * 100,
    }

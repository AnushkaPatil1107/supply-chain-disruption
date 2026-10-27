import random
import numpy as np
from typing import Dict, List, Tuple, NamedTuple
from faker import Faker

# Initialize Faker for generating customer names
fake = Faker()

# Define gym equipment categories with their respective suppliers and manufacturers
# Based on provided list of gym equipment companies
EQUIPMENT_CATEGORIES = {
    'Treadmills': {'suppliers': ['NordicTrack', 'Peloton', 'ProForm', 'Horizon Fitness'], 'manufacturers': ['Technogym', 'Life Fitness', 'Matrix Fitness', 'Star Trac']},
    'Stationary Bikes': {'suppliers': ['Peloton', 'Concept2', 'Schwinn', 'Keiser'], 'manufacturers': ['Cybex International', 'Technogym', 'Precor', 'StairMaster']},
    'Rowing Machines': {'suppliers': ['Concept2', 'Rogue Fitness', 'WaterRower', 'Sunny Health'], 'manufacturers': ['Life Fitness', 'Cybex International', 'Matrix Fitness', 'Technogym']},
    'Elliptical Trainers': {'suppliers': ['NordicTrack', 'REP Fitness', 'Sole Fitness', 'Octane Fitness'], 'manufacturers': ['Technogym', 'Precor', 'Life Fitness', 'Matrix Fitness']},
    'Dumbbells': {'suppliers': ['Bowflex', 'Rogue Fitness', 'PowerBlock', 'SPRI'], 'manufacturers': ['Eleiko', 'Technogym', 'Hampton Fitness', 'CAP Barbell']},
    'Kettlebells': {'suppliers': ['REP Fitness', 'Body-Solid', 'Rogue Fitness', 'Perform Better'], 'manufacturers': ['Technogym', 'Eleiko', 'TRX', 'GoFit']},
    'Barbells': {'suppliers': ['Rogue Fitness', 'Body-Solid', 'American Barbell', 'Titan Fitness'], 'manufacturers': ['Eleiko', 'Force USA', 'Ivanko', 'York Barbell']},
    'Weight Plates': {'suppliers': ['Rogue Fitness', 'REP Fitness', 'Titan Fitness', 'Fringe Sport'], 'manufacturers': ['Eleiko', 'Force USA', 'York Barbell', 'Ivanko']},
    'Power Racks': {'suppliers': ['REP Fitness', 'Body-Solid', 'Titan Fitness', 'Rogue Fitness'], 'manufacturers': ['Technogym', 'Hammer Strength', 'Force USA', 'Cybex International']},
    'Bench Presses': {'suppliers': ['Body-Solid', 'Rogue Fitness', 'REP Fitness', 'Marcy'], 'manufacturers': ['Technogym', 'Eleiko', 'Hammer Strength', 'Matrix Fitness']},
    'Smith Machines': {'suppliers': ['Body-Solid', 'REP Fitness', 'Titan Fitness', 'Force USA'], 'manufacturers': ['Technogym', 'Life Fitness', 'Hammer Strength', 'Matrix Fitness']},
    'Cable Machines': {'suppliers': ['REP Fitness', 'Onnit', 'Body-Solid', 'Titan Fitness'], 'manufacturers': ['Cybex International', 'Technogym', 'Life Fitness', 'Hammer Strength']},
    'Leg Press Machines': {'suppliers': ['Body-Solid', 'Rogue Fitness', 'Titan Fitness', 'TKO'], 'manufacturers': ['Technogym', 'Life Fitness', 'Hammer Strength', 'Matrix Fitness']},
    'Lat Pulldown Machines': {'suppliers': ['REP Fitness', 'Bowflex', 'Body-Solid', 'Titan Fitness'], 'manufacturers': ['Cybex International', 'Precor', 'Hammer Strength', 'Matrix Fitness']},
    'Shoulder Press Machines': {'suppliers': ['REP Fitness', 'Onnit', 'Body-Solid', 'Titan Fitness'], 'manufacturers': ['Cybex International', 'Technogym', 'Life Fitness', 'Hammer Strength']}
}

# Configure suppliers and manufacturers to be unique for each category
SUPPLIERS = {}
MANUFACTURERS = {}

# Instead of grouping, we'll use the specific equipment categories to keep suppliers unique
for category, companies in EQUIPMENT_CATEGORIES.items():
    # Make each category its own group instead of using the broader grouping
    SUPPLIERS[category] = []
    MANUFACTURERS[category] = []
    
    # Add all suppliers from this category with unique names
    for supplier in companies['suppliers']:
        unique_supplier = f"{supplier} ({category})"  # Make each supplier unique to its category
        SUPPLIERS[category].append(unique_supplier)
    
    # Add all manufacturers from this category (potentially with unique names)
    for manufacturer in companies['manufacturers']:
        unique_manufacturer = f"{manufacturer} ({category})"  # Make each manufacturer unique to its category
        MANUFACTURERS[category].append(unique_manufacturer)

# Parameter presets for common supply chain scenarios
class PresetScenario(NamedTuple):
    name: str
    description: str
    suppliers: int
    manufacturers: int
    customers: int
    base_inventory: int
    disruption_probability: float

PRESETS = [
    PresetScenario(
        name="Normal Operations",
        description="Standard supply chain with minimal disruptions",
        suppliers=30,
        manufacturers=30,
        customers=10,
        base_inventory=100,
        disruption_probability=0.1
    ),
    PresetScenario(
        name="Global Pandemic",
        description="Severe disruptions affecting multiple suppliers with limited inventory",
        suppliers=30,
        manufacturers=30,
        customers=15,
        base_inventory=50,
        disruption_probability=0.7
    ),
    PresetScenario(
        name="Regional Crisis",
        description="Moderate disruptions affecting some suppliers",
        suppliers=30,
        manufacturers=30,
        customers=12,
        base_inventory=75,
        disruption_probability=0.4
    ),
    PresetScenario(
        name="Natural Disaster",
        description="Severe but localized disruptions",
        suppliers=30,
        manufacturers=30,
        customers=10,
        base_inventory=60,
        disruption_probability=0.5
    ),
    PresetScenario(
        name="Transportation Strike",
        description="Disruptions in delivery but not in production capacity",
        suppliers=30,
        manufacturers=30,
        customers=15,
        base_inventory=120,
        disruption_probability=0.3
    ),
    PresetScenario(
        name="Maximum Capacity",
        description="Extensive network of suppliers and manufacturers at full capacity",
        suppliers=30,
        manufacturers=30,
        customers=25,
        base_inventory=200,
        disruption_probability=0.2
    ),
    PresetScenario(
        name="Ultra High Volume",
        description="Extremely large network with high-volume data processing",
        suppliers=30,
        manufacturers=30,
        customers=30,
        base_inventory=1000,
        disruption_probability=0.1
    )
]

class SupplyChainNode:
    def __init__(self, name: str, category: str, inventory: int = 100):
        self.name = name
        self.category = category
        self.inventory = inventory
        self.supply_amount = 0

class ManufacturerNode:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category

class SupplyChainSimulation:
    def __init__(self, 
                 num_suppliers: int,
                 num_manufacturers: int,
                 num_customers: int,
                 base_inventory: int = 100,
                 disruption_probability: float = 0.2):
        # Store the disruption probability for later use
        self.disruption_probability = disruption_probability
        
        # Initialize suppliers across categories
        self.suppliers = []
        
        # Handle the case when num_suppliers exceeds available unique suppliers
        total_available_suppliers = 0
        for category in SUPPLIERS:
            total_available_suppliers += len(SUPPLIERS[category])
        
        # Cap the number of suppliers to available ones
        actual_num_suppliers = min(num_suppliers, total_available_suppliers)
        
        # Calculate distribution across categories
        suppliers_per_category = max(1, actual_num_suppliers // len(SUPPLIERS))
        remaining_suppliers = actual_num_suppliers % len(SUPPLIERS)

        for category in SUPPLIERS:
            # Calculate how many suppliers to select for this category
            category_suppliers_count = suppliers_per_category
            if remaining_suppliers > 0:
                category_suppliers_count += 1
                remaining_suppliers -= 1

            # Select suppliers for this category
            available_suppliers = SUPPLIERS[category]
            
            # Make sure we don't try to sample more than available
            category_suppliers_count = min(category_suppliers_count, len(available_suppliers))
            
            if category_suppliers_count > 0:
                selected_suppliers = random.sample(
                    available_suppliers,
                    category_suppliers_count
                )

                for supplier in selected_suppliers:
                    self.suppliers.append(SupplyChainNode(supplier, category, base_inventory))

        # Initialize manufacturers across categories
        self.manufacturers = []
        
        # Handle the case when num_manufacturers exceeds available unique manufacturers
        total_available_manufacturers = 0
        for category in MANUFACTURERS:
            total_available_manufacturers += len(MANUFACTURERS[category])
        
        # Cap the number of manufacturers to available ones
        actual_num_manufacturers = min(num_manufacturers, total_available_manufacturers)
        
        # Calculate distribution across categories
        manufacturers_per_category = max(1, actual_num_manufacturers // len(MANUFACTURERS))
        remaining_manufacturers = actual_num_manufacturers % len(MANUFACTURERS)

        for category in MANUFACTURERS:
            # Calculate how many manufacturers to select for this category
            category_manufacturers_count = manufacturers_per_category
            if remaining_manufacturers > 0:
                category_manufacturers_count += 1
                remaining_manufacturers -= 1

            # Select manufacturers for this category
            available_manufacturers = MANUFACTURERS[category]
            
            # Make sure we don't try to sample more than available
            category_manufacturers_count = min(category_manufacturers_count, len(available_manufacturers))
            
            if category_manufacturers_count > 0:
                selected_manufacturers = random.sample(
                    available_manufacturers,
                    category_manufacturers_count
                )
                
                for manufacturer in selected_manufacturers:
                    self.manufacturers.append(ManufacturerNode(manufacturer, category))

        # Generate random customer names using Faker
        self.fake = Faker()
        self.customers = [self.fake.name() for _ in range(num_customers)]

        # Initialize production and disruption tracking
        self.units_produced = {f"{m.name}_{m.category}": 0 for m in self.manufacturers}
        self.disruptions = {s.name: None for s in self.suppliers}
        self.solutions = {s.name: "No solution provided" for s in self.suppliers}

    def simulate_normal(self) -> Dict:
        """Normal simulation without disruptions"""
        results = {
            'supplier_amounts': {f"{s.name} ({s.category})": s.supply_amount for s in self.suppliers},
            'manufacturer_production': {f"{m.name} ({m.category})": self.units_produced[f"{m.name}_{m.category}"] 
                                     for m in self.manufacturers},
            'customer_received': sum(self.units_produced.values())
        }
        return results

    def simulate_with_disruptions(self) -> Dict:
        """Simulation with disruptions"""
        # Common supply chain disruption types
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
        
        # Check if any disruptions have been manually set
        any_manual_disruptions = any(self.disruptions.values())
        
        # If no manual disruptions set, generate random disruptions based on probability
        if not any_manual_disruptions:
            for supplier in self.suppliers:
                # Apply random disruptions based on the disruption probability
                if random.random() < self.disruption_probability:
                    disruption = random.choice(disruption_types)
                    self.disruptions[supplier.name] = disruption
                    
                    # Also generate a solution for this disruption
                    solutions = [
                        f"Source from alternative supplier",
                        f"Expedite shipment through premium freight",
                        f"Implement temporary production change",
                        f"Activate emergency supply contract",
                        f"Utilize inventory reserves"
                    ]
                    self.solutions[supplier.name] = random.choice(solutions)
        
        # Copy original values for comparison
        original_supply = {f"{s.name} ({s.category})": s.supply_amount for s in self.suppliers}

        # Apply disruptions (reduce supply by 50-80% for disrupted suppliers)
        disrupted_supply = original_supply.copy()
        for supplier in self.suppliers:
            # Check if the supplier has a disruption defined
            if supplier.name in self.disruptions:
                # Vary the impact between suppliers (50-80% reduction)
                reduction_factor = random.uniform(0.2, 0.5)  # Keep 20-50% of original
                disrupted_supply[f"{supplier.name} ({supplier.category})"] *= reduction_factor

        # Calculate reduced production based on supply reductions
        # The more disrupted suppliers in a category, the more impact on manufacturers
        reduced_production = {}
        for manufacturer in self.manufacturers:
            category = manufacturer.category
            # Find suppliers in the same category
            category_suppliers = [s for s in self.suppliers if s.category == category]
            # Count disrupted suppliers in this category
            disrupted_category_suppliers = [s for s in category_suppliers if s.name in self.disruptions]
            
            # Calculate reduction factor based on ratio of disrupted suppliers
            if category_suppliers:
                disruption_ratio = len(disrupted_category_suppliers) / len(category_suppliers)
                # Formula: The more disruptions, the lower the output (min 30% of original)
                production_factor = max(0.3, 1.0 - (disruption_ratio * 0.7))
            else:
                production_factor = 0.7  # Default reduction if no category suppliers
            
            reduced_production[f"{manufacturer.name} ({manufacturer.category})"] = int(
                self.units_produced[f"{manufacturer.name}_{manufacturer.category}"] * production_factor
            )

        results = {
            'supplier_amounts': disrupted_supply,
            'manufacturer_production': reduced_production,
            'customer_received': sum(reduced_production.values()),
            'disruption_events': [
                {'supplier': s.name, 'category': s.category, 'disruption': self.disruptions[s.name]}
                for s in self.suppliers
                if s.name in self.disruptions and self.disruptions[s.name] is not None
            ]
        }
        return results

    def simulate_with_solutions(self) -> Dict:
        """Simulation with solutions to disruptions"""
        solved_supply = {f"{s.name} ({s.category})": s.supply_amount for s in self.suppliers}
        solved_production = {f"{m.name} ({m.category})": self.units_produced[f"{m.name}_{m.category}"] 
                           for m in self.manufacturers}

        # Define phrases that indicate no solution is available
        no_solution_phrases = ["not found", "not available", "no solution", 
                              "unavailable", "unknown", "none", "n/a", "tbd"]
                              
        # Redistribute supply from non-disrupted suppliers within same category
        for category in SUPPLIERS:
            category_suppliers = [s for s in self.suppliers if s.category == category]
            # Only count suppliers as working if they are not disrupted
            working_suppliers = [s for s in category_suppliers if s.name not in self.disruptions]

            for supplier in category_suppliers:
                # Only apply solution if disrupted, has a solution, and there are working suppliers
                solution_text = str(self.solutions.get(supplier.name, "") or "").strip().lower()
                
                # Check if there's a valid solution (not in our no-solution phrases list)
                has_solution = (solution_text and 
                               not any(phrase in solution_text for phrase in no_solution_phrases) and
                               solution_text not in no_solution_phrases)
                
                # Check if supplier is disrupted and has a solution
                if supplier.name in self.disruptions and has_solution and working_suppliers:
                    extra_load = solved_supply[f"{supplier.name} ({supplier.category})"] / len(working_suppliers)
                    for ws in working_suppliers:
                        solved_supply[f"{ws.name} ({ws.category})"] += extra_load

        results = {
            'supplier_amounts': solved_supply,
            'manufacturer_production': solved_production,
            'customer_received': sum(solved_production.values()),
            'solution_events': [
                {
                    'disrupted_supplier': s.name,
                    'category': s.category,
                    'solution': self.solutions.get(s.name, "No solution provided"),
                    'redistributed_to': [ws.name for ws in self.suppliers 
                                      if ws.category == s.category and s.name not in self.disruptions]
                }
                for s in self.suppliers
                if s.name in self.disruptions and s.name in self.solutions
            ]
        }
        return results

def create_sample_chain(
    num_suppliers: int = 3,
    num_manufacturers: int = 2,
    num_customers: int = 2,
    base_inventory: int = 100,
    disruption_probability: float = 0.2
) -> SupplyChainSimulation:
    return SupplyChainSimulation(
        num_suppliers=num_suppliers,
        num_manufacturers=num_manufacturers,
        num_customers=num_customers,
        base_inventory=base_inventory,
        disruption_probability=disruption_probability
    )
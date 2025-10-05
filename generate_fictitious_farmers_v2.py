#!/usr/bin/env python3
"""
Generate 2500 fictitious farmers for AgSense ERP system (Version 2)
This script creates realistic but clearly marked fictitious farmer data
with varied loan amounts, crops, fertilizers, and farming cycles.
Improved to handle email uniqueness and add missing columns.
"""

import random
import sqlite3
from datetime import datetime, timedelta

# Database connection
conn = sqlite3.connect("src/agsense.db")
cursor = conn.cursor()


# First, let's add the missing columns to the farmers table
def add_missing_columns():
    """Add missing columns to the farmers table"""
    try:
        cursor.execute(
            "ALTER TABLE farmers ADD COLUMN loan_status TEXT DEFAULT 'Pending'"
        )
        print("✓ Added loan_status column")
    except sqlite3.OperationalError:
        print("- loan_status column already exists")

    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN loan_amount REAL DEFAULT 0.0")
        print("✓ Added loan_amount column")
    except sqlite3.OperationalError:
        print("- loan_amount column already exists")

    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN crop_season TEXT")
        print("✓ Added crop_season column")
    except sqlite3.OperationalError:
        print("- crop_season column already exists")

    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN fertilizer_type TEXT")
        print("✓ Added fertilizer_type column")
    except sqlite3.OperationalError:
        print("- fertilizer_type column already exists")

    try:
        cursor.execute(
            "ALTER TABLE farmers ADD COLUMN fertilizer_cost REAL DEFAULT 0.0"
        )
        print("✓ Added fertilizer_cost column")
    except sqlite3.OperationalError:
        print("- fertilizer_cost column already exists")

    conn.commit()


# Filipino names for realistic farmer profiles
first_names = [
    "Juan",
    "Maria",
    "Jose",
    "Ana",
    "Pedro",
    "Carmen",
    "Antonio",
    "Rosa",
    "Manuel",
    "Elena",
    "Francisco",
    "Luz",
    "Ricardo",
    "Gloria",
    "Roberto",
    "Esperanza",
    "Carlos",
    "Remedios",
    "Miguel",
    "Dolores",
    "Angel",
    "Concepcion",
    "Fernando",
    "Pilar",
    "Eduardo",
    "Mercedes",
    "Alejandro",
    "Soledad",
    "Rafael",
    "Teresa",
    "Joaquin",
    "Josefa",
    "Sergio",
    "Francisca",
    "Arturo",
    "Isabel",
    "Raul",
    "Antonia",
    "Enrique",
    "Catalina",
    "Gerardo",
    "Rosario",
    "Alberto",
    "Juana",
    "Armando",
    "Manuela",
    "Rodolfo",
    "Petra",
    "Alfredo",
    "Leonor",
    "Emilio",
    "Vicenta",
    "Guillermo",
    "Felipa",
    "Octavio",
    "Gregoria",
    "Salvador",
    "Perfecta",
    "Aurelio",
    "Marcela",
    "Domingo",
    "Felicidad",
    "Teodoro",
    "Purificacion",
    "Mariano",
    "Presentacion",
    "Esteban",
    "Milagros",
    "Leandro",
    "Consolacion",
]

last_names = [
    "Santos",
    "Reyes",
    "Cruz",
    "Bautista",
    "Ocampo",
    "Garcia",
    "Mendoza",
    "Torres",
    "Tomas",
    "Andres",
    "Marquez",
    "Romualdez",
    "Mercado",
    "Aguilar",
    "Dela Cruz",
    "Ramos",
    "Villanueva",
    "Aquino",
    "Valdez",
    "Soriano",
    "Castillo",
    "Jimenez",
    "Morales",
    "Herrera",
    "Perez",
    "Flores",
    "Gonzales",
    "Rivera",
    "Gomez",
    "Fernandez",
    "Lopez",
    "Hernandez",
    "Diaz",
    "Moreno",
    "Muñoz",
    "Alvarez",
    "Romero",
    "Gutierrez",
    "Navarro",
    "Ruiz",
    "Cabrera",
    "Bravo",
    "Prieto",
    "Molina",
    "Blanco",
    "Guerrero",
    "Cortez",
    "Medina",
    "Campos",
    "Contreras",
    "Vargas",
    "Figueroa",
    "Espinoza",
    "Sandoval",
    "Salazar",
    "Soto",
    "Maldonado",
    "Esquivel",
    "Jimenez",
    "Cordova",
]

# Philippine provinces and municipalities
locations = [
    {
        "province": "Nueva Ecija",
        "municipality": "Cabanatuan",
        "barangay": "Sangitan East",
    },
    {"province": "Nueva Ecija", "municipality": "Gapan", "barangay": "San Vicente"},
    {"province": "Nueva Ecija", "municipality": "San Jose", "barangay": "Kaliwanagan"},
    {"province": "Pangasinan", "municipality": "Dagupan", "barangay": "Bonuan Binloc"},
    {"province": "Pangasinan", "municipality": "Urdaneta", "barangay": "Nancayasan"},
    {"province": "Pangasinan", "municipality": "Malasiqui", "barangay": "Apatot"},
    {"province": "Iloilo", "municipality": "Iloilo City", "barangay": "Jaro"},
    {"province": "Iloilo", "municipality": "Pototan", "barangay": "Naslo"},
    {"province": "Iloilo", "municipality": "Lambunao", "barangay": "Poblacion"},
    {
        "province": "Negros Occidental",
        "municipality": "Bacolod",
        "barangay": "Taculing",
    },
    {
        "province": "Negros Occidental",
        "municipality": "Silay",
        "barangay": "Guinhalaran",
    },
    {"province": "Negros Occidental", "municipality": "Talisay", "barangay": "Zone 14"},
    {"province": "Camarines Sur", "municipality": "Naga", "barangay": "Triangulo"},
    {"province": "Camarines Sur", "municipality": "Iriga", "barangay": "San Agustin"},
    {"province": "Camarines Sur", "municipality": "Pili", "barangay": "Anayan"},
    {"province": "Isabela", "municipality": "Ilagan", "barangay": "Marana"},
    {"province": "Isabela", "municipality": "Santiago", "barangay": "Sinsayon"},
    {"province": "Isabela", "municipality": "Cauayan", "barangay": "District II"},
    {"province": "Cagayan", "municipality": "Tuguegarao", "barangay": "Caritan Centro"},
    {"province": "Cagayan", "municipality": "Aparri", "barangay": "Macanaya"},
    {"province": "Bukidnon", "municipality": "Malaybalay", "barangay": "Casisang"},
    {"province": "Bukidnon", "municipality": "Valencia", "barangay": "Poblacion"},
    {"province": "South Cotabato", "municipality": "Koronadal", "barangay": "Zone I"},
    {
        "province": "South Cotabato",
        "municipality": "General Santos",
        "barangay": "Dadiangas North",
    },
]

# Crop types with seasonal information
crops = [
    {
        "name": "Rice",
        "season": "Wet",
        "cycle_months": 4,
        "typical_yield_per_hectare": 4.5,
    },
    {
        "name": "Rice",
        "season": "Dry",
        "cycle_months": 3.5,
        "typical_yield_per_hectare": 5.2,
    },
    {
        "name": "Corn",
        "season": "Wet",
        "cycle_months": 4,
        "typical_yield_per_hectare": 3.8,
    },
    {
        "name": "Corn",
        "season": "Dry",
        "cycle_months": 3.5,
        "typical_yield_per_hectare": 4.2,
    },
    {
        "name": "Sugarcane",
        "season": "Plant",
        "cycle_months": 12,
        "typical_yield_per_hectare": 65,
    },
    {
        "name": "Sugarcane",
        "season": "Ratoon",
        "cycle_months": 10,
        "typical_yield_per_hectare": 55,
    },
    {
        "name": "Coconut",
        "season": "Year-round",
        "cycle_months": 12,
        "typical_yield_per_hectare": 1.2,
    },
    {
        "name": "Banana",
        "season": "Year-round",
        "cycle_months": 12,
        "typical_yield_per_hectare": 25,
    },
    {
        "name": "Mango",
        "season": "Dry",
        "cycle_months": 6,
        "typical_yield_per_hectare": 8.5,
    },
    {
        "name": "Coffee",
        "season": "Dry",
        "cycle_months": 6,
        "typical_yield_per_hectare": 1.8,
    },
    {
        "name": "Cacao",
        "season": "Year-round",
        "cycle_months": 12,
        "typical_yield_per_hectare": 0.8,
    },
    {
        "name": "Sweet Potato",
        "season": "Dry",
        "cycle_months": 3,
        "typical_yield_per_hectare": 12,
    },
    {
        "name": "Cassava",
        "season": "Wet",
        "cycle_months": 8,
        "typical_yield_per_hectare": 18,
    },
    {
        "name": "Peanut",
        "season": "Dry",
        "cycle_months": 3.5,
        "typical_yield_per_hectare": 2.2,
    },
    {
        "name": "Soybean",
        "season": "Wet",
        "cycle_months": 3,
        "typical_yield_per_hectare": 1.8,
    },
]

# Fertilizer types with costs
fertilizers = [
    {"name": "Urea (46-0-0)", "cost_per_bag": 1250, "application_rate_per_hectare": 3},
    {
        "name": "Complete (14-14-14)",
        "cost_per_bag": 1180,
        "application_rate_per_hectare": 4,
    },
    {
        "name": "Ammosul (21-0-0)",
        "cost_per_bag": 980,
        "application_rate_per_hectare": 3.5,
    },
    {
        "name": "Muriate of Potash (0-0-60)",
        "cost_per_bag": 1350,
        "application_rate_per_hectare": 2,
    },
    {
        "name": "DAP (18-46-0)",
        "cost_per_bag": 1420,
        "application_rate_per_hectare": 2.5,
    },
    {
        "name": "NPK (16-16-16)",
        "cost_per_bag": 1200,
        "application_rate_per_hectare": 3.5,
    },
    {
        "name": "Organic Compost",
        "cost_per_bag": 180,
        "application_rate_per_hectare": 20,
    },
    {"name": "Chicken Manure", "cost_per_bag": 120, "application_rate_per_hectare": 25},
    {
        "name": "Foliar Fertilizer",
        "cost_per_bag": 850,
        "application_rate_per_hectare": 1,
    },
    {
        "name": "Lime (Agricultural)",
        "cost_per_bag": 95,
        "application_rate_per_hectare": 10,
    },
]

# Loan status options
loan_statuses = [
    "Approved",
    "Pending",
    "Under Review",
    "Disbursed",
    "Partially Disbursed",
    "Completed",
]

# AgScore ranges based on farmer performance
agscore_ranges = {
    "Excellent": (850, 950),
    "Very Good": (750, 849),
    "Good": (650, 749),
    "Fair": (550, 649),
    "Poor": (400, 549),
    "New": (500, 600),  # New farmers start with moderate score
}


def generate_unique_email(first_name, last_name, attempt=0):
    """Generate a unique email address"""
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    if attempt == 0:
        email = f"{first_name.lower()}.{last_name.lower()}.fictitious@{random.choice(domains)}"
    else:
        email = f"{first_name.lower()}.{last_name.lower()}.{attempt}.fictitious@{random.choice(domains)}"

    # Check if email already exists
    cursor.execute("SELECT id FROM farmers WHERE email = ?", (email,))
    if cursor.fetchone():
        return generate_unique_email(first_name, last_name, attempt + 1)

    return email


def generate_phone_number():
    """Generate a realistic Philippine mobile number"""
    prefixes = [
        "0917",
        "0918",
        "0919",
        "0920",
        "0921",
        "0922",
        "0923",
        "0924",
        "0925",
        "0926",
        "0927",
        "0928",
        "0929",
    ]
    return f"{random.choice(prefixes)}{random.randint(1000000, 9999999)}"


def calculate_loan_amount(crop, farm_size, fertilizer):
    """Calculate realistic loan amount based on crop, farm size, and fertilizer needs"""
    base_cost_per_hectare = {
        "Rice": 35000,
        "Corn": 28000,
        "Sugarcane": 85000,
        "Coconut": 15000,
        "Banana": 45000,
        "Mango": 25000,
        "Coffee": 20000,
        "Cacao": 18000,
        "Sweet Potato": 22000,
        "Cassava": 18000,
        "Peanut": 25000,
        "Soybean": 20000,
    }

    base_cost = base_cost_per_hectare.get(crop["name"], 25000)
    fertilizer_cost = (
        fertilizer["cost_per_bag"]
        * fertilizer["application_rate_per_hectare"]
        * farm_size
    )

    total_cost = (base_cost * farm_size) + fertilizer_cost

    # Add some variation (±20%)
    variation = random.uniform(0.8, 1.2)
    return round(total_cost * variation, 2)


def generate_farmer_data():
    """Generate a single farmer's data"""
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    location = random.choice(locations)
    crop = random.choice(crops)
    fertilizer = random.choice(fertilizers)

    # Farm size between 0.5 and 5 hectares (realistic for small farmers)
    farm_size = round(random.uniform(0.5, 5.0), 2)

    # Generate AgScore based on weighted distribution
    score_category = random.choices(
        list(agscore_ranges.keys()),
        weights=[10, 20, 35, 25, 8, 2],  # Most farmers in Good to Very Good range
        k=1,
    )[0]
    agscore = random.randint(*agscore_ranges[score_category])

    # Calculate loan amount
    loan_amount = calculate_loan_amount(crop, farm_size, fertilizer)

    # Calculate fertilizer cost
    fertilizer_cost = (
        fertilizer["cost_per_bag"]
        * fertilizer["application_rate_per_hectare"]
        * farm_size
    )

    # Generate dates
    registration_date = datetime.now() - timedelta(days=random.randint(30, 730))
    last_activity = registration_date + timedelta(days=random.randint(1, 30))

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": generate_unique_email(first_name, last_name),
        "phone": generate_phone_number(),
        "address": f"Barangay {location['barangay']}, {location['municipality']}, {location['province']}",
        "farm_size": farm_size,
        "crop_type": crop["name"],
        "crop_season": crop["season"],
        "fertilizer_type": fertilizer["name"],
        "fertilizer_cost": fertilizer_cost,
        "loan_amount": loan_amount,
        "loan_status": random.choice(loan_statuses),
        "agscore": agscore,
        "registration_date": registration_date.strftime("%Y-%m-%d"),
        "last_activity": last_activity.strftime("%Y-%m-%d"),
        "notes": f"FICTITIOUS DATA - Generated for testing purposes. Crop: {crop['name']} ({crop['season']} season), Fertilizer: {fertilizer['name']}",
    }


def insert_farmer(farmer_data):
    """Insert farmer data into the database"""
    try:
        cursor.execute(
            """
            INSERT INTO farmers (
                first_name, last_name, email, phone, address, farm_size,
                crop_type, crop_season, fertilizer_type, fertilizer_cost,
                loan_amount, loan_status, agscore, registration_date, last_activity, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                farmer_data["first_name"],
                farmer_data["last_name"],
                farmer_data["email"],
                farmer_data["phone"],
                farmer_data["address"],
                farmer_data["farm_size"],
                farmer_data["crop_type"],
                farmer_data["crop_season"],
                farmer_data["fertilizer_type"],
                farmer_data["fertilizer_cost"],
                farmer_data["loan_amount"],
                farmer_data["loan_status"],
                farmer_data["agscore"],
                farmer_data["registration_date"],
                farmer_data["last_activity"],
                farmer_data["notes"],
            ),
        )
        return cursor.lastrowid
    except Exception as e:
        print(f"Error inserting farmer: {e}")
        return None


def main():
    """Generate and insert 2500 fictitious farmers"""
    print("Adding missing columns to farmers table...")
    add_missing_columns()

    print("\nGenerating remaining fictitious farmers...")

    # Check how many farmers already exist
    cursor.execute("SELECT COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%'")
    existing_count = cursor.fetchone()[0]

    remaining_to_generate = max(0, 2500 - existing_count)
    print(f"Existing fictitious farmers: {existing_count}")
    print(f"Remaining to generate: {remaining_to_generate}")

    if remaining_to_generate == 0:
        print("Already have 2500 or more fictitious farmers!")
        return

    successful_inserts = 0
    failed_inserts = 0

    for i in range(remaining_to_generate):
        if i % 100 == 0:
            print(f"Progress: {i}/{remaining_to_generate} farmers generated...")

        farmer_data = generate_farmer_data()
        farmer_id = insert_farmer(farmer_data)

        if farmer_id:
            successful_inserts += 1
        else:
            failed_inserts += 1

    # Commit all changes
    conn.commit()

    print("\nGeneration complete!")
    print(f"Successfully inserted: {successful_inserts} farmers")
    print(f"Failed inserts: {failed_inserts} farmers")

    # Generate summary statistics
    cursor.execute("SELECT COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%'")
    fictitious_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT crop_type, COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%' GROUP BY crop_type"
    )
    crop_distribution = cursor.fetchall()

    cursor.execute(
        "SELECT loan_status, COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%' GROUP BY loan_status"
    )
    loan_distribution = cursor.fetchall()

    cursor.execute(
        "SELECT AVG(loan_amount), MIN(loan_amount), MAX(loan_amount) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%'"
    )
    loan_stats = cursor.fetchone()

    print("\n=== SUMMARY STATISTICS ===")
    print(f"Total fictitious farmers: {fictitious_count}")
    print("\nLoan Amount Statistics:")
    print(f"  Average: ₱{loan_stats[0]:,.2f}")
    print(f"  Minimum: ₱{loan_stats[1]:,.2f}")
    print(f"  Maximum: ₱{loan_stats[2]:,.2f}")

    print("\nCrop Distribution:")
    for crop, count in crop_distribution:
        print(f"  {crop}: {count} farmers")

    print("\nLoan Status Distribution:")
    for status, count in loan_distribution:
        print(f"  {status}: {count} farmers")

    conn.close()


if __name__ == "__main__":
    main()

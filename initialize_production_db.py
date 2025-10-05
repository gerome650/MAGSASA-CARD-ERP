#!/usr/bin/env python3
"""
Initialize production database with enhanced Philippine agricultural data
This script ensures the database has the correct enhanced data for deployment
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

# Filipino first names (common names)
FILIPINO_FIRST_NAMES = [
    "Jose",
    "Maria",
    "Juan",
    "Ana",
    "Antonio",
    "Carmen",
    "Francisco",
    "Luz",
    "Manuel",
    "Rosa",
    "Pedro",
    "Elena",
    "Carlos",
    "Josefa",
    "Luis",
    "Esperanza",
    "Miguel",
    "Remedios",
    "Angel",
    "Concepcion",
    "Roberto",
    "Pilar",
    "Ricardo",
    "Dolores",
    "Eduardo",
    "Mercedes",
    "Fernando",
    "Gloria",
    "Alejandro",
    "Cristina",
    "Ramon",
    "Teresita",
    "Alfredo",
    "Rosario",
    "Ernesto",
    "Soledad",
    "Arturo",
    "Corazon",
    "Rodolfo",
    "Milagros",
    "Raul",
    "Natividad",
    "Armando",
    "Leonor",
    "Rogelio",
    "Pacita",
    "Danilo",
    "Lourdes",
    "Reynaldo",
    "Norma",
]

FILIPINO_LAST_NAMES = [
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
    "Castillo",
    "Iglesias",
    "Villanueva",
    "Ramos",
    "Romero",
    "Lazaro",
    "Gonzales",
    "Aquino",
    "Flores",
    "Valdez",
    "Roque",
    "Gutierrez",
    "Tolentino",
    "Santiago",
    "Soriano",
    "Pascual",
    "Hernandez",
    "Dela Cruz",
    "Morales",
]

# Philippine locations
PHILIPPINE_LOCATIONS = [
    "Nueva Ecija - Cabanatuan City, Central Luzon, Luzon",
    "Isabela - Ilagan City, Cagayan Valley, Luzon",
    "Bukidnon - Malaybalay City, Northern Mindanao, Mindanao",
    "Negros Oriental - Dumaguete City, Central Visayas, Visayas",
    "Iloilo - Iloilo City, Western Visayas, Visayas",
    "Davao del Sur - Davao City, Davao Region, Mindanao",
    "Pangasinan - Lingayen, Ilocos Region, Luzon",
    "Leyte - Tacloban City, Eastern Visayas, Visayas",
    "South Cotabato - Koronadal City, SOCCSKSARGEN, Mindanao",
    "Laguna - Santa Cruz, CALABARZON, Luzon",
]

# Philippine crops
PHILIPPINE_CROPS = [
    "Rice",
    "Corn",
    "Sugarcane",
    "Coconut",
    "Banana",
    "Coffee",
    "Cacao",
    "Mango",
    "Vegetables",
    "Rubber",
]

# Mobile number prefixes
MOBILE_PREFIXES = [
    "0917",
    "0918",
    "0919",
    "0920",
    "0921",
    "0928",
    "0929",
    "0939",
    "0908",
    "0909",
    "0910",
    "0912",
    "0930",
    "0938",
    "0946",
    "0947",
]


def create_production_database():
    """Create and populate production database"""
    db_path = "src/agsense.db"

    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Removed existing database")

    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create farmers table with correct schema
    cursor.execute(
        """
        CREATE TABLE farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            mobile_number TEXT,
            government_id TEXT,
            address TEXT,
            land_size_ha REAL,
            crop_types TEXT,
            land_tenure TEXT,
            farming_experience INTEGER,
            agscore INTEGER,
            agscore_grade TEXT,
            loan_amount REAL,
            loan_status TEXT,
            risk_factors TEXT,
            registration_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    print("✅ Created farmers table")

    # Generate and insert farmers
    farmers_data = []
    for _i in range(1, 2501):  # Generate 2500 farmers
        first_name = random.choice(FILIPINO_FIRST_NAMES)
        last_name = random.choice(FILIPINO_LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        # Generate realistic data
        location = random.choice(PHILIPPINE_LOCATIONS)
        land_size = round(random.uniform(0.5, 5.0), 1)
        farming_experience = random.randint(1, 25)

        # Crop selection
        num_crops = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        selected_crops = random.sample(PHILIPPINE_CROPS, num_crops)
        crop_types = ", ".join(selected_crops)

        # Contact info
        mobile_prefix = random.choice(MOBILE_PREFIXES)
        mobile_suffix = "".join([str(random.randint(0, 9)) for _ in range(7)])
        mobile_number = f"{mobile_prefix}{mobile_suffix}"

        email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}.fictitious@agsense.ph"

        # AgScore and loan data
        agscore = random.randint(400, 900)
        if agscore >= 800:
            agscore_grade = "Excellent"
            loan_status = random.choice(["Approved", "Disbursed", "Repaying"])
            loan_amount = random.randint(80000, 200000)
        elif agscore >= 650:
            agscore_grade = "Good"
            loan_status = random.choice(["Approved", "Pending", "Under Review"])
            loan_amount = random.randint(50000, 150000)
        elif agscore >= 500:
            agscore_grade = "Fair"
            loan_status = random.choice(["Pending", "Under Review", "Approved"])
            loan_amount = random.randint(30000, 100000)
        else:
            agscore_grade = "Poor"
            loan_status = random.choice(["Pending", "Rejected", "Under Review"])
            loan_amount = random.randint(20000, 80000)

        land_tenure = random.choices(
            ["Titled owner", "Owner-cultivator", "Leaseholder", "Tenant"],
            weights=[20, 40, 25, 15],
        )[0]

        # Registration date
        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now()
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        registration_date = start_date + timedelta(days=random_days)

        farmer_data = (
            full_name,
            first_name,
            last_name,
            email,
            mobile_number,
            f"SSS-{random.randint(10, 99)}-{random.randint(1000000, 9999999)}-{random.randint(0, 9)}",
            location,
            land_size,
            crop_types,
            land_tenure,
            farming_experience,
            agscore,
            agscore_grade,
            loan_amount,
            loan_status,
            "FICTITIOUS DATA - Generated for testing",
            registration_date.date(),
            "FICTITIOUS DATA - Generated for testing and demonstration purposes",
        )

        farmers_data.append(farmer_data)

    # Insert all farmers
    cursor.executemany(
        """
        INSERT INTO farmers (
            full_name, first_name, last_name, email, mobile_number, government_id,
            address, land_size_ha, crop_types, land_tenure, farming_experience,
            agscore, agscore_grade, loan_amount, loan_status, risk_factors,
            registration_date, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        farmers_data,
    )

    conn.commit()

    # Verify data
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total_farmers = cursor.fetchone()[0]

    cursor.execute(
        "SELECT full_name, address, crop_types, agscore FROM farmers LIMIT 3"
    )
    samples = cursor.fetchall()

    print(f"✅ Created {total_farmers} Filipino farmers")
    print("👥 Sample farmers:")
    for farmer in samples:
        print(
            f"   {farmer[0]} - {farmer[1][:50]}... - {farmer[2]} - AgScore: {farmer[3]}"
        )

    conn.close()
    print("🎉 Production database initialized successfully!")


if __name__ == "__main__":
    create_production_database()

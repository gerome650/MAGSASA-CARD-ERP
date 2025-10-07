#!/usr/bin/env python3
"""
Deployment script to initialize database with fictitious farmers
This script should be run in the deployed environment
"""

import random
import sqlite3
from datetime import datetime, timedelta


def create_database_schema(_):
    """Create the database schema"""
    conn = sqlite3.connect("src/agsense.db")
    cursor = conn.cursor()

    # Create farmers table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            address TEXT,
            farm_size REAL,
            crop_type TEXT,
            crop_season TEXT,
            fertilizer_type TEXT,
            fertilizer_cost REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0,
            loan_status TEXT DEFAULT 'Pending',
            agscore INTEGER DEFAULT 500,
            registration_date TEXT,
            last_activity TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create other tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            price REAL,
            cost REAL,
            stock_quantity INTEGER DEFAULT 0,
            unit TEXT,
            supplier_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            total_amount REAL,
            status TEXT DEFAULT 'Pending',
            order_date TEXT,
            delivery_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            status TEXT DEFAULT 'Active',
            commission_rate REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print("✓ Database schema created")


def populate_sample_data(_):
    """Populate the database with sample data"""
    conn = sqlite3.connect("src/agsense.db")
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM farmers")
    existing_farmers = cursor.fetchone()[0]

    if existing_farmers > 0:
        print(f"Database already has {existing_farmers} farmers")
        conn.close()
        return

    # Sample data for quick deployment
    sample_farmers = [
        (
            "Juan",
            "Santos",
            "juan.santos.demo@fictitious.com",
            "09171234567",
            "Cabanatuan, Nueva Ecija",
            2.5,
            "Rice",
            "Wet",
            "Urea (46-0-0)",
            3750.0,
            87500.0,
            "Approved",
            750,
        ),
        (
            "Maria",
            "Cruz",
            "maria.cruz.demo@fictitious.com",
            "09181234567",
            "Dagupan, Pangasinan",
            1.8,
            "Corn",
            "Dry",
            "Complete (14-14-14)",
            8496.0,
            50400.0,
            "Disbursed",
            820,
        ),
        (
            "Pedro",
            "Reyes",
            "pedro.reyes.demo@fictitious.com",
            "09191234567",
            "Iloilo City, Iloilo",
            3.2,
            "Sugarcane",
            "Plant",
            "NPK (16-16-16)",
            13440.0,
            272000.0,
            "Pending",
            680,
        ),
        (
            "Ana",
            "Garcia",
            "ana.garcia.demo@fictitious.com",
            "09201234567",
            "Bacolod, Negros Occidental",
            1.5,
            "Banana",
            "Year-round",
            "Organic Compost",
            5400.0,
            67500.0,
            "Under Review",
            710,
        ),
        (
            "Jose",
            "Mendoza",
            "jose.mendoza.demo@fictitious.com",
            "09211234567",
            "Naga, Camarines Sur",
            2.0,
            "Coconut",
            "Year-round",
            "Chicken Manure",
            6000.0,
            30000.0,
            "Approved",
            650,
        ),
    ]

    # Insert sample farmers
    for _i, farmer_data in enumerate(sample_farmers):
        reg_date = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime(
            "%Y-%m-%d"
        )
        last_activity = (
            datetime.now() - timedelta(days=random.randint(1, 30))
        ).strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT INTO farmers (
                first_name, last_name, email, phone, address, farm_size,
                crop_type, crop_season, fertilizer_type, fertilizer_cost,
                loan_amount, loan_status, agscore, registration_date, last_activity,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            farmer_data
            + (reg_date, last_activity, "DEMO DATA - Sample farmer for testing"),
        )

    # Generate additional farmers to reach 2500
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
    ]
    last_names = [
        "Santos",
        "Cruz",
        "Reyes",
        "Garcia",
        "Mendoza",
        "Torres",
        "Flores",
        "Ramos",
        "Aquino",
        "Valdez",
    ]
    crops = [
        "Rice",
        "Corn",
        "Sugarcane",
        "Banana",
        "Coconut",
        "Coffee",
        "Cacao",
        "Mango",
    ]

    for i in range(2495):  # 2500 - 5 sample farmers
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}.{i}.demo@fictitious.com"
        phone = f"0917{random.randint(1000000, 9999999)}"
        address = f"Barangay {i+1}, Sample Municipality, Sample Province"
        farm_size = round(random.uniform(0.5, 5.0), 2)
        crop_type = random.choice(crops)
        loan_amount = round(random.uniform(10000, 200000), 2)
        agscore = random.randint(400, 950)

        reg_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime(
            "%Y-%m-%d"
        )
        last_activity = (
            datetime.now() - timedelta(days=random.randint(1, 30))
        ).strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT INTO farmers (
                first_name, last_name, email, phone, address, farm_size,
                crop_type, loan_amount, agscore, registration_date, last_activity,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                first_name,
                last_name,
                email,
                phone,
                address,
                farm_size,
                crop_type,
                loan_amount,
                agscore,
                reg_date,
                last_activity,
                "DEMO DATA - Generated for testing",
            ),
        )

    conn.commit()

    # Verify data
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total_farmers = cursor.fetchone()[0]

    conn.close()
    print(f"✓ Populated database with {total_farmers} farmers")


def main(_):
    """Main deployment function"""
    print("Initializing AgSense ERP Database...")
    print("=" * 50)

    create_database_schema()
    populate_sample_data()

    print("=" * 50)
    print("Database initialization complete!")
    print("The system now has 2500 fictitious farmers ready for testing.")


if __name__ == "__main__":
    main()

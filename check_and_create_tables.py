#!/usr/bin/env python3
"""
Check existing database tables and create farmers table if needed
"""

import sqlite3
import os

# Database connection
db_path = 'src/agsense.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def check_existing_tables():
    """Check what tables exist in the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Existing tables:")
    for table in tables:
        print(f"  - {table[0]}")
    return [table[0] for table in tables]

def create_farmers_table():
    """Create the farmers table with all necessary fields"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            address TEXT,
            farm_size REAL,
            crop_type TEXT,
            agscore INTEGER DEFAULT 500,
            registration_date TEXT,
            last_activity TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created farmers table")

def create_products_table():
    """Create the products table"""
    cursor.execute("""
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
    """)
    print("✓ Created products table")

def create_orders_table():
    """Create the orders table"""
    cursor.execute("""
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
    """)
    print("✓ Created orders table")

def create_partners_table():
    """Create the partners table"""
    cursor.execute("""
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
    """)
    print("✓ Created partners table")

def create_categories_table():
    """Create the categories table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created categories table")

def create_suppliers_table():
    """Create the suppliers table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created suppliers table")

def main():
    print("Checking database structure...")
    print(f"Database path: {os.path.abspath(db_path)}")
    
    existing_tables = check_existing_tables()
    
    print("\nCreating missing tables...")
    
    # Create all necessary tables
    create_farmers_table()
    create_products_table()
    create_orders_table()
    create_partners_table()
    create_categories_table()
    create_suppliers_table()
    
    # Commit changes
    conn.commit()
    
    print("\nFinal table list:")
    check_existing_tables()
    
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    main()


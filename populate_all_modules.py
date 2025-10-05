#!/usr/bin/env python3
"""
Populate all modules with sample data for AgSense ERP
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta


def populate_all_modules():
    """Populate products, orders, partners, and related data"""
    db_path = "src/agsense.db"

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🌾 Populating AgSense ERP with comprehensive sample data...")

    # 1. Create and populate categories
    print("📂 Creating product categories...")
    categories = [
        ("Fertilizers", "Organic and synthetic fertilizers for crop nutrition"),
        ("Seeds", "High-quality seeds for various crops"),
        ("Pesticides", "Crop protection products"),
        ("Tools", "Farming tools and equipment"),
        ("Irrigation", "Water management and irrigation systems"),
    ]

    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute(
        """
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.executemany(
        """
        INSERT INTO categories (name, description) VALUES (?, ?)
    """,
        categories,
    )

    # 2. Create and populate suppliers
    print("🏭 Creating suppliers...")
    suppliers = [
        (
            "AgriCorp Philippines",
            "Leading agricultural supplier in the Philippines",
            "Manila",
            "09171234567",
            "info@agricorp.ph",
        ),
        (
            "FarmTech Solutions",
            "Modern farming technology and equipment",
            "Cebu",
            "09181234567",
            "sales@farmtech.ph",
        ),
        (
            "GreenGrow Supplies",
            "Organic fertilizers and sustainable farming",
            "Davao",
            "09191234567",
            "contact@greengrow.ph",
        ),
        (
            "Harvest Pro",
            "Professional farming tools and equipment",
            "Iloilo",
            "09201234567",
            "support@harvestpro.ph",
        ),
        (
            "CropCare Inc",
            "Crop protection and pest management",
            "Cagayan de Oro",
            "09211234567",
            "info@cropcare.ph",
        ),
    ]

    cursor.execute("DROP TABLE IF EXISTS suppliers")
    cursor.execute(
        """
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location TEXT,
            contact_number TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.executemany(
        """
        INSERT INTO suppliers (name, description, location, contact_number, email)
        VALUES (?, ?, ?, ?, ?)
    """,
        suppliers,
    )

    # 3. Create and populate products
    print("🌱 Creating products...")
    products_data = [
        # Fertilizers
        (
            "Urea 46-0-0",
            1,
            1,
            "High nitrogen fertilizer for leafy growth",
            1250.00,
            1500.00,
            500,
            50,
            "kg",
        ),
        (
            "Complete 14-14-14",
            1,
            1,
            "Balanced NPK fertilizer for all crops",
            1800.00,
            2200.00,
            300,
            30,
            "kg",
        ),
        (
            "Organic Compost",
            1,
            3,
            "Premium organic fertilizer",
            800.00,
            1200.00,
            200,
            20,
            "kg",
        ),
        (
            "Phosphate Rock",
            1,
            1,
            "Natural phosphorus source",
            950.00,
            1300.00,
            150,
            15,
            "kg",
        ),
        # Seeds
        (
            "Hybrid Rice IR64",
            2,
            2,
            "High-yielding rice variety",
            180.00,
            250.00,
            1000,
            100,
            "kg",
        ),
        (
            "Corn Pioneer 30G12",
            2,
            2,
            "Premium hybrid corn seeds",
            320.00,
            450.00,
            800,
            80,
            "kg",
        ),
        (
            "Tomato Determinate",
            2,
            4,
            "High-quality tomato seeds",
            2500.00,
            3500.00,
            50,
            5,
            "pack",
        ),
        (
            "Lettuce Grand Rapids",
            2,
            4,
            "Fast-growing lettuce variety",
            450.00,
            650.00,
            100,
            10,
            "pack",
        ),
        # Pesticides
        (
            "Roundup Herbicide",
            3,
            5,
            "Broad-spectrum herbicide",
            850.00,
            1200.00,
            200,
            20,
            "liter",
        ),
        (
            "Malathion Insecticide",
            3,
            5,
            "Effective insect control",
            650.00,
            950.00,
            150,
            15,
            "liter",
        ),
        (
            "Copper Fungicide",
            3,
            5,
            "Organic fungal disease control",
            750.00,
            1100.00,
            100,
            10,
            "liter",
        ),
        # Tools
        (
            "Hand Tractor 8HP",
            4,
            2,
            "Compact farming tractor",
            85000.00,
            120000.00,
            20,
            2,
            "unit",
        ),
        (
            "Water Pump 3HP",
            4,
            2,
            "Irrigation water pump",
            25000.00,
            35000.00,
            30,
            3,
            "unit",
        ),
        (
            "Sprayer Knapsack",
            4,
            4,
            "Manual pesticide sprayer",
            2500.00,
            3500.00,
            100,
            10,
            "unit",
        ),
        (
            "Harvesting Sickle",
            4,
            4,
            "Traditional harvesting tool",
            350.00,
            500.00,
            200,
            20,
            "unit",
        ),
        # Irrigation
        (
            "Drip Irrigation Kit",
            5,
            2,
            "Water-efficient irrigation system",
            15000.00,
            22000.00,
            50,
            5,
            "set",
        ),
        (
            "Sprinkler System",
            5,
            2,
            "Automated sprinkler irrigation",
            12000.00,
            18000.00,
            40,
            4,
            "set",
        ),
        (
            "PVC Pipes 4-inch",
            5,
            1,
            "Irrigation pipe system",
            450.00,
            650.00,
            500,
            50,
            "meter",
        ),
    ]

    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            supplier_id INTEGER,
            description TEXT,
            cost_price REAL,
            selling_price REAL,
            stock_quantity INTEGER,
            reorder_level INTEGER,
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.executemany(
        """
        INSERT INTO products (name, category_id, supplier_id, description, cost_price, selling_price,
                            stock_quantity, reorder_level, unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        products_data,
    )

    # 4. Create and populate partners
    print("🤝 Creating partners...")
    partners_data = [
        (
            "LBC Express",
            "Logistics",
            "Last-Mile Delivery",
            "Juan Dela Cruz",
            "operations@lbc.ph",
            "09171111111",
            5.5,
            "Net 15",
            "Metro Manila, Luzon",
            "Active",
        ),
        (
            "2GO Express",
            "Logistics",
            "Provincial Delivery",
            "Maria Santos",
            "logistics@2go.ph",
            "09182222222",
            6.0,
            "Net 30",
            "Nationwide",
            "Active",
        ),
        (
            "JRS Express",
            "Logistics",
            "Same-Day Delivery",
            "Pedro Reyes",
            "sameday@jrs.ph",
            "09193333333",
            7.5,
            "Net 7",
            "Metro Manila",
            "Active",
        ),
        (
            "AgriLogistics Pro",
            "Logistics",
            "Bulk Agricultural Transport",
            "Ana Garcia",
            "bulk@agrilogistics.ph",
            "09204444444",
            4.5,
            "Net 45",
            "Luzon, Visayas",
            "Active",
        ),
        (
            "FarmLink Distributors",
            "Supplier",
            "Agricultural Equipment",
            "Carlos Mendoza",
            "sales@farmlink.ph",
            "09215555555",
            8.0,
            "Net 30",
            "Nationwide",
            "Active",
        ),
    ]

    cursor.execute("DROP TABLE IF EXISTS partners")
    cursor.execute(
        """
        CREATE TABLE partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            category TEXT,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            commission_rate REAL,
            payment_terms TEXT,
            geographic_coverage TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.executemany(
        """
        INSERT INTO partners (name, type, category, contact_person, email, phone,
                            commission_rate, payment_terms, geographic_coverage, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        partners_data,
    )

    # 5. Create and populate orders
    print("📦 Creating orders...")

    # Get farmer IDs
    cursor.execute(
        "SELECT id FROM farmers LIMIT 100"
    )  # Use first 100 farmers for orders
    farmer_ids = [row[0] for row in cursor.fetchall()]

    # Get product IDs and prices
    cursor.execute("SELECT id, selling_price FROM products")
    products = cursor.fetchall()

    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            order_date DATE,
            status TEXT,
            total_amount REAL,
            delivery_address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute(
        """
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_price REAL
        )
    """
    )

    orders_data = []
    order_items_data = []
    order_id = 1

    # Generate 450 orders (to match dashboard stats)
    for _i in range(450):
        farmer_id = random.choice(farmer_ids)

        # Random order date within last 6 months
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        order_date = start_date + timedelta(days=random_days)

        status = random.choices(
            ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"],
            weights=[20, 15, 10, 25, 25, 5],
        )[0]

        # Generate order items (1-4 products per order)
        num_items = random.randint(1, 4)
        selected_products = random.sample(products, num_items)

        total_amount = 0
        for product_id, selling_price in selected_products:
            quantity = random.randint(1, 10)
            unit_price = selling_price
            total_price = quantity * unit_price
            total_amount += total_price

            order_items_data.append(
                (order_id, product_id, quantity, unit_price, total_price)
            )

        orders_data.append(
            (
                farmer_id,
                order_date.date(),
                status,
                total_amount,
                f"Farm Address for Farmer {farmer_id}",
                f"Order #{order_id} - Generated sample data",
            )
        )

        order_id += 1

    cursor.executemany(
        """
        INSERT INTO orders (farmer_id, order_date, status, total_amount, delivery_address, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        orders_data,
    )

    cursor.executemany(
        """
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
        VALUES (?, ?, ?, ?, ?)
    """,
        order_items_data,
    )

    conn.commit()

    # Verify data
    cursor.execute("SELECT COUNT(*) FROM categories")
    categories_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM suppliers")
    suppliers_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM partners")
    partners_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM order_items")
    order_items_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status != 'Cancelled'")
    total_revenue = cursor.fetchone()[0] or 0

    print("\n✅ Database populated successfully!")
    print(f"📂 Categories: {categories_count}")
    print(f"🏭 Suppliers: {suppliers_count}")
    print(f"🌱 Products: {products_count}")
    print(f"🤝 Partners: {partners_count}")
    print(f"📦 Orders: {orders_count}")
    print(f"📋 Order Items: {order_items_count}")
    print(f"💰 Total Revenue: ₱{total_revenue:,.2f}")

    conn.close()


if __name__ == "__main__":
    populate_all_modules()

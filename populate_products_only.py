#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.category import Category
from src.models.product import Product
from src.models.supplier import Supplier
from src.models.user import db


def populate_products_only():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        print("🚀 Starting product catalog population...")

        # Clear existing product data
        Product.query.delete()
        Supplier.query.delete()
        Category.query.delete()

        # 1. Create categories
        print("📂 Creating product categories...")
        categories_data = [
            {"name": "Fertilizers", "description": "Chemical and organic fertilizers"},
            {"name": "Seeds", "description": "High-quality seeds for various crops"},
            {"name": "Pesticides", "description": "Pest control products"},
            {"name": "Tools", "description": "Farming tools and equipment"},
            {"name": "Irrigation", "description": "Irrigation systems and supplies"},
        ]

        categories = []
        for cat_data in categories_data:
            category = Category(**cat_data)
            db.session.add(category)
            categories.append(category)

        db.session.flush()
        print(f"✅ Created {len(categories)} categories")

        # 2. Create suppliers
        print("🏢 Creating suppliers...")
        suppliers_data = [
            {
                "name": "Atlas Fertilizer Corporation",
                "contact_person": "John Smith",
                "email": "sales@atlas.com.ph",
                "phone": "02-8123-4567",
                "address": "Makati City, Metro Manila",
            },
            {
                "name": "East-West Seed Company",
                "contact_person": "Jane Doe",
                "email": "orders@ewseed.com",
                "phone": "02-8234-5678",
                "address": "Lipa City, Batangas",
            },
            {
                "name": "Bayer CropScience",
                "contact_person": "Mike Johnson",
                "email": "sales@bayer.com.ph",
                "phone": "02-8345-6789",
                "address": "Taguig City, Metro Manila",
            },
        ]

        suppliers = []
        for sup_data in suppliers_data:
            supplier = Supplier(**sup_data)
            db.session.add(supplier)
            suppliers.append(supplier)

        db.session.flush()
        print(f"✅ Created {len(suppliers)} suppliers")

        # 3. Create products
        print("🌱 Creating products...")
        products_data = [
            {
                "name": "Complete Fertilizer 14-14-14",
                "sku": "FERT-14-14-14",
                "description": "Balanced NPK fertilizer for all crops",
                "category_id": categories[0].id,
                "supplier_id": suppliers[0].id,
                "cost_price": 850.00,
                "selling_price": 950.00,
                "stock_on_hand": 500,
                "reorder_point": 50,
                "uom": "bag",
                "unit_value": 50,
            },
            {
                "name": "Hybrid Rice Seeds IR64",
                "sku": "SEED-RICE-IR64",
                "description": "High-yielding hybrid rice variety",
                "category_id": categories[1].id,
                "supplier_id": suppliers[1].id,
                "cost_price": 120.00,
                "selling_price": 150.00,
                "stock_on_hand": 200,
                "reorder_point": 20,
                "uom": "kg",
                "unit_value": 1,
            },
            {
                "name": "Urea Fertilizer 46-0-0",
                "sku": "FERT-UREA-46",
                "description": "High nitrogen content fertilizer",
                "category_id": categories[0].id,
                "supplier_id": suppliers[0].id,
                "cost_price": 1200.00,
                "selling_price": 1350.00,
                "stock_on_hand": 300,
                "reorder_point": 30,
                "uom": "bag",
                "unit_value": 50,
            },
            {
                "name": "Insecticide Cypermethrin",
                "sku": "PEST-CYPER-250",
                "description": "Broad spectrum insecticide",
                "category_id": categories[2].id,
                "supplier_id": suppliers[2].id,
                "cost_price": 450.00,
                "selling_price": 520.00,
                "stock_on_hand": 150,
                "reorder_point": 15,
                "uom": "liter",
                "unit_value": 1,
            },
            {
                "name": "Hand Tractor Plow",
                "sku": "TOOL-PLOW-HT",
                "description": "Heavy-duty plow for hand tractors",
                "category_id": categories[3].id,
                "supplier_id": suppliers[0].id,
                "cost_price": 8500.00,
                "selling_price": 9500.00,
                "stock_on_hand": 25,
                "reorder_point": 5,
                "uom": "piece",
                "unit_value": 1,
            },
            {
                "name": "Organic Compost",
                "sku": "FERT-COMPOST-ORG",
                "description": "Premium organic compost for soil improvement",
                "category_id": categories[0].id,
                "supplier_id": suppliers[0].id,
                "cost_price": 250.00,
                "selling_price": 300.00,
                "stock_on_hand": 100,
                "reorder_point": 20,
                "uom": "bag",
                "unit_value": 25,
            },
            {
                "name": "Corn Seeds Hybrid",
                "sku": "SEED-CORN-HYB",
                "description": "High-yield hybrid corn seeds",
                "category_id": categories[1].id,
                "supplier_id": suppliers[1].id,
                "cost_price": 180.00,
                "selling_price": 220.00,
                "stock_on_hand": 80,
                "reorder_point": 15,
                "uom": "kg",
                "unit_value": 1,
            },
            {
                "name": "Herbicide Glyphosate",
                "sku": "PEST-GLYPH-500",
                "description": "Systemic herbicide for weed control",
                "category_id": categories[2].id,
                "supplier_id": suppliers[2].id,
                "cost_price": 320.00,
                "selling_price": 380.00,
                "stock_on_hand": 60,
                "reorder_point": 10,
                "uom": "liter",
                "unit_value": 1,
            },
        ]

        products = []
        for prod_data in products_data:
            product = Product(**prod_data)
            db.session.add(product)
            products.append(product)

        # Commit all changes
        db.session.commit()

        print(f"✅ Created {len(products)} products")

        # Print comprehensive summary
        print("\n🎉 Product Catalog Population Completed Successfully!")
        print("📊 Summary:")
        print(f"  • Categories: {len(categories)}")
        print(f"  • Suppliers: {len(suppliers)}")
        print(f"  • Products: {len(products)}")

        # Calculate total inventory value
        total_value = sum(
            float(product.selling_price) * product.stock_on_hand for product in products
        )
        print(f"\n💰 Total Inventory Value: ₱{total_value:,.2f}")


if __name__ == "__main__":
    populate_products_only()

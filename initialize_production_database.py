#!/usr/bin/env python3
"""
Initialize production database with all required data
This script creates tables and populates them with sample data
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask

from src.database import db
from src.models.category import Category
from src.models.partner import Partner
from src.models.product import Product
from src.models.supplier import Supplier
from src.models.user import Role, User


def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'agsense.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def initialize_database():
    """Initialize database with all tables and sample data"""
    app = create_app()

    with app.app_context():
        print("🗄️  Creating database tables...")
        db.drop_all()  # Start fresh
        db.create_all()

        print("👥 Creating user roles and permissions...")
        # Create roles and permissions (simplified for now)
        admin_role = Role(name="Super Admin", description="Full system access")
        db.session.add(admin_role)

        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@agsense.com",
            first_name="System",
            last_name="Administrator",
            role_id=1,
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)

        print("📂 Creating product categories...")
        categories = [
            Category(name="Fertilizers", description="Soil nutrients and fertilizers"),
            Category(name="Seeds", description="Crop seeds and planting materials"),
            Category(name="Pesticides", description="Pest control products"),
            Category(name="Tools", description="Farming tools and equipment"),
            Category(name="Irrigation", description="Water management systems"),
        ]
        for category in categories:
            db.session.add(category)

        print("🏭 Creating suppliers...")
        suppliers = [
            Supplier(
                name="AgriCorp Philippines",
                contact_person="Juan Dela Cruz",
                email="juan@agricorp.ph",
                phone="09171234567",
                address="Manila, Philippines",
                status="Active",
            ),
            Supplier(
                name="FarmTech Solutions",
                contact_person="Maria Santos",
                email="maria@farmtech.ph",
                phone="09181234567",
                address="Cebu, Philippines",
                status="Active",
            ),
            Supplier(
                name="GreenGrow Supplies",
                contact_person="Pedro Reyes",
                email="pedro@greengrow.ph",
                phone="09191234567",
                address="Davao, Philippines",
                status="Active",
            ),
            Supplier(
                name="CropCare Inc",
                contact_person="Ana Garcia",
                email="ana@cropcare.ph",
                phone="09201234567",
                address="Iloilo, Philippines",
                status="Active",
            ),
            Supplier(
                name="HarvestMax Ltd",
                contact_person="Carlos Mendoza",
                email="carlos@harvestmax.ph",
                phone="09211234567",
                address="Cagayan de Oro, Philippines",
                status="Active",
            ),
        ]
        for supplier in suppliers:
            db.session.add(supplier)

        db.session.commit()  # Commit to get IDs

        print("🌱 Creating products...")
        products = [
            # Fertilizers
            Product(
                sku="FERT-001",
                name="Complete Fertilizer 14-14-14",
                description="Balanced NPK fertilizer for all crops",
                brand="AgriCorp",
                category_id=1,
                uom="kg",
                unit_value=50,
                status="Active",
                supplier_id=1,
                cost_price=1200,
                selling_price=1500,
                stock_on_hand=100,
                reorder_point=20,
            ),
            Product(
                sku="FERT-002",
                name="Urea 46-0-0",
                description="High nitrogen fertilizer",
                brand="FarmTech",
                category_id=1,
                uom="kg",
                unit_value=50,
                status="Active",
                supplier_id=2,
                cost_price=1100,
                selling_price=1400,
                stock_on_hand=150,
                reorder_point=30,
            ),
            Product(
                sku="FERT-003",
                name="Organic Compost",
                description="Natural organic fertilizer",
                brand="GreenGrow",
                category_id=1,
                uom="kg",
                unit_value=25,
                status="Active",
                supplier_id=3,
                cost_price=800,
                selling_price=1000,
                stock_on_hand=80,
                reorder_point=15,
            ),
            # Seeds
            Product(
                sku="SEED-001",
                name="Hybrid Rice Seeds",
                description="High-yield rice variety",
                brand="CropCare",
                category_id=2,
                uom="kg",
                unit_value=20,
                status="Active",
                supplier_id=4,
                cost_price=2500,
                selling_price=3000,
                stock_on_hand=50,
                reorder_point=10,
            ),
            Product(
                sku="SEED-002",
                name="Corn Seeds (Yellow)",
                description="Sweet corn variety",
                brand="HarvestMax",
                category_id=2,
                uom="kg",
                unit_value=10,
                status="Active",
                supplier_id=5,
                cost_price=1800,
                selling_price=2200,
                stock_on_hand=75,
                reorder_point=15,
            ),
            Product(
                sku="SEED-003",
                name="Vegetable Seeds Mix",
                description="Mixed vegetable seeds",
                brand="AgriCorp",
                category_id=2,
                uom="pack",
                unit_value=1,
                status="Active",
                supplier_id=1,
                cost_price=150,
                selling_price=200,
                stock_on_hand=200,
                reorder_point=50,
            ),
            # Pesticides
            Product(
                sku="PEST-001",
                name="Insecticide Spray",
                description="Broad spectrum insecticide",
                brand="FarmTech",
                category_id=3,
                uom="liter",
                unit_value=1,
                status="Active",
                supplier_id=2,
                cost_price=800,
                selling_price=1000,
                stock_on_hand=60,
                reorder_point=12,
            ),
            Product(
                sku="PEST-002",
                name="Fungicide Powder",
                description="Disease control fungicide",
                brand="GreenGrow",
                category_id=3,
                uom="kg",
                unit_value=1,
                status="Active",
                supplier_id=3,
                cost_price=1200,
                selling_price=1500,
                stock_on_hand=40,
                reorder_point=8,
            ),
            Product(
                sku="PEST-003",
                name="Herbicide Solution",
                description="Weed control herbicide",
                brand="CropCare",
                category_id=3,
                uom="liter",
                unit_value=1,
                status="Active",
                supplier_id=4,
                cost_price=900,
                selling_price=1200,
                stock_on_hand=35,
                reorder_point=7,
            ),
            # Tools
            Product(
                sku="TOOL-001",
                name="Hand Trowel",
                description="Gardening hand tool",
                brand="HarvestMax",
                category_id=4,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=5,
                cost_price=250,
                selling_price=350,
                stock_on_hand=120,
                reorder_point=25,
            ),
            Product(
                sku="TOOL-002",
                name="Pruning Shears",
                description="Plant pruning tool",
                brand="AgriCorp",
                category_id=4,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=1,
                cost_price=450,
                selling_price=600,
                stock_on_hand=80,
                reorder_point=15,
            ),
            Product(
                sku="TOOL-003",
                name="Watering Can",
                description="5-liter watering can",
                brand="FarmTech",
                category_id=4,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=2,
                cost_price=300,
                selling_price=400,
                stock_on_hand=90,
                reorder_point=18,
            ),
            # Irrigation
            Product(
                sku="IRRI-001",
                name="Drip Irrigation Kit",
                description="Complete drip irrigation system",
                brand="GreenGrow",
                category_id=5,
                uom="set",
                unit_value=1,
                status="Active",
                supplier_id=3,
                cost_price=2500,
                selling_price=3200,
                stock_on_hand=25,
                reorder_point=5,
            ),
            Product(
                sku="IRRI-002",
                name="Sprinkler Head",
                description="Adjustable sprinkler head",
                brand="CropCare",
                category_id=5,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=4,
                cost_price=180,
                selling_price=250,
                stock_on_hand=150,
                reorder_point=30,
            ),
            Product(
                sku="IRRI-003",
                name="Garden Hose 25m",
                description="Flexible garden hose",
                brand="HarvestMax",
                category_id=5,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=5,
                cost_price=800,
                selling_price=1100,
                stock_on_hand=45,
                reorder_point=10,
            ),
            # Additional products
            Product(
                sku="FERT-004",
                name="Potassium Sulfate",
                description="Potassium fertilizer",
                brand="AgriCorp",
                category_id=1,
                uom="kg",
                unit_value=25,
                status="Active",
                supplier_id=1,
                cost_price=1300,
                selling_price=1600,
                stock_on_hand=70,
                reorder_point=15,
            ),
            Product(
                sku="SEED-004",
                name="Tomato Seeds",
                description="Cherry tomato variety",
                brand="FarmTech",
                category_id=2,
                uom="pack",
                unit_value=1,
                status="Active",
                supplier_id=2,
                cost_price=120,
                selling_price=180,
                stock_on_hand=180,
                reorder_point=40,
            ),
            Product(
                sku="TOOL-004",
                name="Garden Rake",
                description="Metal garden rake",
                brand="GreenGrow",
                category_id=4,
                uom="piece",
                unit_value=1,
                status="Active",
                supplier_id=3,
                cost_price=350,
                selling_price=500,
                stock_on_hand=65,
                reorder_point=12,
            ),
        ]

        for product in products:
            db.session.add(product)

        print("🤝 Creating partners...")
        partners = [
            Partner(
                name="Manila Logistics Hub",
                partner_type="Logistics",
                contact_person="Roberto Cruz",
                email="roberto@manilalogistics.ph",
                phone="09171111111",
                address="Manila, Philippines",
                status="Active",
            ),
            Partner(
                name="Cebu Distribution Center",
                partner_type="Logistics",
                contact_person="Carmen Santos",
                email="carmen@cebudist.ph",
                phone="09181111111",
                address="Cebu, Philippines",
                status="Active",
            ),
            Partner(
                name="Mindanao Freight Services",
                partner_type="Logistics",
                contact_person="Diego Reyes",
                email="diego@mindanaofreight.ph",
                phone="09191111111",
                address="Davao, Philippines",
                status="Active",
            ),
            Partner(
                name="Island Express Delivery",
                partner_type="Logistics",
                contact_person="Elena Garcia",
                email="elena@islandexpress.ph",
                phone="09201111111",
                address="Iloilo, Philippines",
                status="Active",
            ),
            Partner(
                name="Northern Luzon Transport",
                partner_type="Logistics",
                contact_person="Fernando Mendoza",
                email="fernando@northernluzon.ph",
                phone="09211111111",
                address="Tuguegarao, Philippines",
                status="Active",
            ),
        ]

        for partner in partners:
            db.session.add(partner)

        db.session.commit()

        print("✅ Database initialized successfully!")
        print("📊 Created:")
        print(f"   - {len(categories)} categories")
        print(f"   - {len(suppliers)} suppliers")
        print(f"   - {len(products)} products")
        print(f"   - {len(partners)} partners")
        print("   - 1 admin user")


if __name__ == "__main__":
    initialize_database()

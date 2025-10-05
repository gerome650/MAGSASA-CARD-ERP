#!/usr/bin/env python3
"""
Add sample orders and partners data to the database
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
from datetime import datetime, timedelta

from flask import Flask

from src.database import db
from src.models.farmer import Farmer
from src.models.order import Order, OrderItem
from src.models.partner import Partner
from src.models.product import Product


def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'agsense.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def add_sample_orders():
    """Add sample orders to the database"""
    app = create_app()

    with app.app_context():
        print("📦 Adding sample orders...")

        # Get existing farmers and products
        farmers = Farmer.query.limit(50).all()  # Use first 50 farmers
        products = Product.query.all()

        if not farmers or not products:
            print(
                "❌ No farmers or products found. Please run the database initialization first."
            )
            return

        order_statuses = [
            "Pending",
            "Confirmed",
            "Processing",
            "Shipped",
            "Delivered",
            "Cancelled",
        ]

        # Create 25 sample orders
        for i in range(25):
            farmer = random.choice(farmers)

            # Create order
            order = Order(
                order_number=f"ORD-{datetime.now().strftime('%Y%m')}-{str(i+1).zfill(4)}",
                farmer_id=farmer.id,
                status=random.choice(order_statuses),
                total_amount=0,  # Will be calculated from items
                notes=f"Sample order for {farmer.first_name} {farmer.last_name}",
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            )

            db.session.add(order)
            db.session.flush()  # Get the order ID

            # Add 1-4 random products to each order
            num_items = random.randint(1, 4)
            total_amount = 0

            for _j in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                unit_price = product.selling_price
                unit_cost = product.cost_price
                total_price = quantity * unit_price
                total_cost = quantity * unit_cost
                margin = total_price - total_cost

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    total_price=total_price,
                    total_cost=total_cost,
                    margin=margin,
                )

                db.session.add(order_item)
                total_amount += total_price

            # Update order total
            order.total_amount = total_amount

        db.session.commit()
        print("✅ Added 25 sample orders")


def add_sample_partners():
    """Add sample partners to the database"""
    app = create_app()

    with app.app_context():
        print("🤝 Adding sample partners...")

        # Check if partners already exist
        existing_partners = Partner.query.count()
        if existing_partners >= 10:
            print(f"ℹ️  {existing_partners} partners already exist, skipping...")
            return

        sample_partners = [
            {
                "name": "Metro Manila Logistics",
                "partner_type": "Logistics",
                "contact_person": "Juan Carlos",
                "email": "juan@metrologistics.ph",
                "phone": "09171234567",
                "address": "Quezon City, Metro Manila",
                "status": "Active",
            },
            {
                "name": "Cebu Express Delivery",
                "partner_type": "Logistics",
                "contact_person": "Maria Gonzales",
                "email": "maria@cebuexpress.ph",
                "phone": "09181234567",
                "address": "Cebu City, Cebu",
                "status": "Active",
            },
            {
                "name": "Davao Freight Services",
                "partner_type": "Logistics",
                "contact_person": "Pedro Santos",
                "email": "pedro@davaofreight.ph",
                "phone": "09191234567",
                "address": "Davao City, Davao del Sur",
                "status": "Active",
            },
            {
                "name": "AgriFinance Corporation",
                "partner_type": "Financial",
                "contact_person": "Ana Reyes",
                "email": "ana@agrifinance.ph",
                "phone": "09201234567",
                "address": "Makati City, Metro Manila",
                "status": "Active",
            },
            {
                "name": "FarmTech Solutions Inc",
                "partner_type": "Technology",
                "contact_person": "Carlos Mendoza",
                "email": "carlos@farmtech.ph",
                "phone": "09211234567",
                "address": "Taguig City, Metro Manila",
                "status": "Active",
            },
            {
                "name": "Rural Insurance Group",
                "partner_type": "Insurance",
                "contact_person": "Elena Cruz",
                "email": "elena@ruralinsurance.ph",
                "phone": "09221234567",
                "address": "Pasig City, Metro Manila",
                "status": "Active",
            },
            {
                "name": "Luzon Agricultural Supplies",
                "partner_type": "Supplier",
                "contact_person": "Roberto Garcia",
                "email": "roberto@luzonagri.ph",
                "phone": "09231234567",
                "address": "Nueva Ecija",
                "status": "Active",
            },
            {
                "name": "Visayas Crop Protection",
                "partner_type": "Supplier",
                "contact_person": "Carmen Lopez",
                "email": "carmen@visayascrop.ph",
                "phone": "09241234567",
                "address": "Iloilo City, Iloilo",
                "status": "Active",
            },
            {
                "name": "Mindanao Seed Bank",
                "partner_type": "Supplier",
                "contact_person": "Diego Fernandez",
                "email": "diego@mindanaoseeds.ph",
                "phone": "09251234567",
                "address": "Cagayan de Oro City",
                "status": "Pending",
            },
            {
                "name": "Island Connect Logistics",
                "partner_type": "Logistics",
                "contact_person": "Sofia Ramirez",
                "email": "sofia@islandconnect.ph",
                "phone": "09261234567",
                "address": "Palawan",
                "status": "Inactive",
            },
        ]

        for partner_data in sample_partners:
            partner = Partner(
                name=partner_data["name"],
                partner_type=partner_data["partner_type"],
                contact_person=partner_data["contact_person"],
                email=partner_data["email"],
                phone=partner_data["phone"],
                address=partner_data["address"],
                status=partner_data["status"],
                created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
            )

            db.session.add(partner)

        db.session.commit()
        print(f"✅ Added {len(sample_partners)} sample partners")


def main():
    """Main function to add all sample data"""
    print("🚀 Adding sample orders and partners data...")
    add_sample_orders()
    add_sample_partners()
    print("✅ Sample data added successfully!")


if __name__ == "__main__":
    main()

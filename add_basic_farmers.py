#!/usr/bin/env python3
"""
Add basic farmers for testing if none exist
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import db
from src.models.user import User, Role, Permission
from src.models.farmer import Farmer
from src.models.category import Category
from src.models.supplier import Supplier
from src.models.product import Product
from src.models.order import Order, OrderItem
from src.models.partner import Partner
from flask import Flask
from datetime import datetime
import random

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'agsense.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def add_basic_farmers():
    """Add basic farmers if none exist"""
    app = create_app()
    
    with app.app_context():
        farmer_count = Farmer.query.count()
        print(f"Current farmers in database: {farmer_count}")
        
        if farmer_count > 0:
            print("Farmers already exist, skipping...")
            return farmer_count
        
        print("Adding basic farmers...")
        
        # Sample Filipino names and locations
        first_names = ['Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Carmen', 'Luis', 'Rosa', 'Carlos', 'Elena']
        last_names = ['Santos', 'Reyes', 'Cruz', 'Garcia', 'Mendoza', 'Lopez', 'Gonzales', 'Fernandez', 'Torres', 'Ramirez']
        locations = [
            'Nueva Ecija', 'Tarlac', 'Bulacan', 'Isabela', 'Pangasinan',
            'Iloilo', 'Negros Occidental', 'Cebu', 'Leyte', 'Samar',
            'Davao del Sur', 'Bukidnon', 'Cotabato', 'Lanao del Norte', 'Misamis Oriental'
        ]
        crops = ['Rice', 'Corn', 'Sugarcane', 'Coconut', 'Banana', 'Vegetables', 'Coffee', 'Cacao']
        
        for i in range(50):  # Add 50 basic farmers
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            farmer = Farmer(
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}.{i+1}@fictitious.com",
                mobile_number=f"0917{random.randint(1000000, 9999999)}",
                address=f"Barangay {random.randint(1, 50)}, {random.choice(locations)}",
                land_size_ha=round(random.uniform(0.5, 5.0), 2),
                crop_types=random.choice(crops),
                agscore=random.randint(300, 850),
                agscore_grade=random.choice(['A', 'B', 'C', 'D']),
                loan_amount=round(random.uniform(5000, 50000), 2),
                loan_status=random.choice(['Pending', 'Approved', 'Disbursed', 'Under Review']),
                notes="FICTITIOUS DATA - Generated for testing purposes"
            )
            
            db.session.add(farmer)
        
        db.session.commit()
        print("✅ Added 50 basic farmers")
        return 50

if __name__ == '__main__':
    add_basic_farmers()


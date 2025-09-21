import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db
from src.models.farmer import Farmer
from src.models.product import Product
from src.models.partner import Partner
from src.models.order import Order, OrderItem
from src.main import app

with app.app_context():
    # Create all tables first
    db.create_all()
    
    # Add sample farmers
    farmers_data = [
        {'name': 'Juan Dela Cruz', 'location': 'Laguna', 'barangay': 'San Pedro', 'crop_type': 'Rice', 'land_size_ha': 2.5, 'agscore': 85, 'loan_status': 'Approved', 'loan_amount': 50000, 'phone': '+63917123456'},
        {'name': 'Maria Santos', 'location': 'Batangas', 'barangay': 'Poblacion', 'crop_type': 'Corn', 'land_size_ha': 1.8, 'agscore': 78, 'loan_status': 'Disbursed', 'loan_amount': 35000, 'phone': '+63918234567'},
        {'name': 'Pedro Reyes', 'location': 'Cavite', 'barangay': 'Silang', 'crop_type': 'Vegetables', 'land_size_ha': 0.5, 'agscore': 92, 'loan_status': 'Pending', 'loan_amount': 15000, 'phone': '+63919345678'},
        {'name': 'Ana Garcia', 'location': 'Rizal', 'barangay': 'Antipolo', 'crop_type': 'Rice', 'land_size_ha': 3.2, 'agscore': 88, 'loan_status': 'Approved', 'loan_amount': 65000, 'phone': '+63920456789'},
        {'name': 'Carlos Mendoza', 'location': 'Quezon', 'barangay': 'Lucena', 'crop_type': 'Corn', 'land_size_ha': 4.1, 'agscore': 75, 'loan_status': 'Repaid', 'loan_amount': 80000, 'phone': '+63921567890'}
    ]
    
    for farmer_data in farmers_data:
        farmer = Farmer(**farmer_data)
        db.session.add(farmer)
    
    # Add sample products
    products_data = [
        {'name': 'Complete Fertilizer 14-14-14', 'category': 'Fertilizer', 'brand': 'Atlas', 'unit': 'bag', 'cost_price': 1200, 'selling_price': 1500, 'stock_quantity': 100, 'description': 'Complete fertilizer for rice and corn'},
        {'name': 'Urea 46-0-0', 'category': 'Fertilizer', 'brand': 'Philphos', 'unit': 'bag', 'cost_price': 1800, 'selling_price': 2200, 'stock_quantity': 75, 'description': 'High nitrogen fertilizer'},
        {'name': 'Hybrid Rice Seeds', 'category': 'Seeds', 'brand': 'SL Agritech', 'unit': 'kg', 'cost_price': 180, 'selling_price': 220, 'stock_quantity': 200, 'description': 'High-yielding hybrid rice variety'},
        {'name': 'Corn Seeds NK6410', 'category': 'Seeds', 'brand': 'Syngenta', 'unit': 'bag', 'cost_price': 3500, 'selling_price': 4200, 'stock_quantity': 50, 'description': 'Premium hybrid corn seeds'},
        {'name': 'Hand Sprayer 16L', 'category': 'Tools', 'brand': 'Yamaha', 'unit': 'piece', 'cost_price': 2500, 'selling_price': 3200, 'stock_quantity': 25, 'description': 'Manual knapsack sprayer'},
        {'name': 'Organic Fertilizer', 'category': 'Fertilizer', 'brand': 'Harbest', 'unit': 'bag', 'cost_price': 800, 'selling_price': 1000, 'stock_quantity': 8, 'description': 'Organic compost fertilizer'}
    ]
    
    for product_data in products_data:
        margin_percentage = ((product_data['selling_price'] - product_data['cost_price']) / product_data['cost_price']) * 100
        product_data['margin_percentage'] = margin_percentage
        product = Product(**product_data)
        db.session.add(product)
    
    # Add sample partners
    partners_data = [
        {'name': 'FastTrack Logistics', 'company_name': 'FastTrack Delivery Corp', 'partner_type': 'Logistics', 'contact_person': 'Roberto Cruz', 'phone': '+63922678901', 'email': 'roberto@fasttrack.ph', 'commission_rate': 8.5, 'performance_rating': 4.2, 'total_orders': 45, 'successful_deliveries': 42},
        {'name': 'Green Valley Supplies', 'company_name': 'Green Valley Agricultural Supplies Inc', 'partner_type': 'Supplier', 'contact_person': 'Linda Tan', 'phone': '+63923789012', 'email': 'linda@greenvalley.ph', 'commission_rate': 12.0, 'performance_rating': 4.5, 'total_orders': 78, 'successful_deliveries': 76},
        {'name': 'AgriHub Solutions', 'company_name': 'AgriHub Solutions Ltd', 'partner_type': 'Both', 'contact_person': 'Michael Wong', 'phone': '+63924890123', 'email': 'michael@agrihub.ph', 'commission_rate': 10.0, 'performance_rating': 4.0, 'total_orders': 32, 'successful_deliveries': 30}
    ]
    
    for partner_data in partners_data:
        partner = Partner(**partner_data)
        db.session.add(partner)
    
    db.session.commit()
    print('Sample data added successfully!')


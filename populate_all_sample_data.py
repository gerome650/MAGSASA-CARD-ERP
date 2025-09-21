#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import random
from src.models.user import db
from src.models.farmer import Farmer
from src.models.category import Category
from src.models.supplier import Supplier
from src.models.product import Product
from src.models.order import Order, OrderItem
from src.main import app

def populate_all_sample_data():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("🚀 Starting comprehensive sample data population...")
        
        # Clear existing data
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        Supplier.query.delete()
        Category.query.delete()
        Farmer.query.delete()
        
        # 1. Create sample farmers
        print("👨‍🌾 Creating sample farmers...")
        sample_farmers = [
            {
                'full_name': 'Juan Dela Cruz',
                'mobile_number': '09171234567',
                'email': 'juan@example.com',
                'barangay': 'San Jose',
                'land_size_ha': 2.5,
                'farming_experience': 15,
                'crop_types': 'Rice, Corn',
                'digital_wallet': '09171234567',
                'agscore': 85,
                'agscore_grade': 'A',
                'loan_status': 'Approved'
            },
            {
                'full_name': 'Maria Santos',
                'mobile_number': '09181234567',
                'email': 'maria@example.com',
                'barangay': 'Poblacion',
                'land_size_ha': 1.8,
                'farming_experience': 12,
                'crop_types': 'Rice, Vegetables',
                'digital_wallet': '09181234567',
                'agscore': 78,
                'agscore_grade': 'B',
                'loan_status': 'Disbursed'
            },
            {
                'full_name': 'Pedro Reyes',
                'mobile_number': '09191234567',
                'email': 'pedro@example.com',
                'barangay': 'Bagong Silang',
                'land_size_ha': 3.2,
                'farming_experience': 20,
                'crop_types': 'Corn, Sugarcane',
                'digital_wallet': '09191234567',
                'agscore': 92,
                'agscore_grade': 'A',
                'loan_status': 'Repaying'
            },
            {
                'full_name': 'Ana Garcia',
                'mobile_number': '09201234567',
                'email': 'ana@example.com',
                'barangay': 'San Antonio',
                'land_size_ha': 1.5,
                'farming_experience': 8,
                'crop_types': 'Rice, Tomatoes',
                'digital_wallet': '09201234567',
                'agscore': 72,
                'agscore_grade': 'B',
                'loan_status': 'Pending'
            },
            {
                'full_name': 'Roberto Cruz',
                'mobile_number': '09211234567',
                'email': 'roberto@example.com',
                'barangay': 'Malamig',
                'land_size_ha': 4.1,
                'farming_experience': 25,
                'crop_types': 'Rice, Corn, Coconut',
                'digital_wallet': '09211234567',
                'agscore': 88,
                'agscore_grade': 'A',
                'loan_status': 'Repaid'
            }
        ]
        
        farmers = []
        for farmer_data in sample_farmers:
            farmer = Farmer(**farmer_data)
            db.session.add(farmer)
            farmers.append(farmer)
        
        db.session.flush()
        print(f"✅ Created {len(farmers)} sample farmers")
        
        # 2. Create categories
        print("📂 Creating product categories...")
        categories_data = [
            {'name': 'Fertilizers', 'description': 'Chemical and organic fertilizers'},
            {'name': 'Seeds', 'description': 'High-quality seeds for various crops'},
            {'name': 'Pesticides', 'description': 'Pest control products'},
            {'name': 'Tools', 'description': 'Farming tools and equipment'},
            {'name': 'Irrigation', 'description': 'Irrigation systems and supplies'}
        ]
        
        categories = []
        for cat_data in categories_data:
            category = Category(**cat_data)
            db.session.add(category)
            categories.append(category)
        
        db.session.flush()
        print(f"✅ Created {len(categories)} categories")
        
        # 3. Create suppliers
        print("🏢 Creating suppliers...")
        suppliers_data = [
            {
                'name': 'Atlas Fertilizer Corporation',
                'contact_person': 'John Smith',
                'email': 'sales@atlas.com.ph',
                'phone': '02-8123-4567',
                'address': 'Makati City, Metro Manila'
            },
            {
                'name': 'East-West Seed Company',
                'contact_person': 'Jane Doe',
                'email': 'orders@ewseed.com',
                'phone': '02-8234-5678',
                'address': 'Lipa City, Batangas'
            },
            {
                'name': 'Bayer CropScience',
                'contact_person': 'Mike Johnson',
                'email': 'sales@bayer.com.ph',
                'phone': '02-8345-6789',
                'address': 'Taguig City, Metro Manila'
            }
        ]
        
        suppliers = []
        for sup_data in suppliers_data:
            supplier = Supplier(**sup_data)
            db.session.add(supplier)
            suppliers.append(supplier)
        
        db.session.flush()
        print(f"✅ Created {len(suppliers)} suppliers")
        
        # 4. Create products
        print("🌱 Creating products...")
        products_data = [
            {
                'name': 'Complete Fertilizer 14-14-14',
                'sku': 'FERT-14-14-14',
                'description': 'Balanced NPK fertilizer for all crops',
                'category_id': categories[0].id,
                'supplier_id': suppliers[0].id,
                'cost_price': 850.00,
                'selling_price': 950.00,
                'stock_on_hand': 500,
                'reorder_point': 50,
                'uom': 'bag',
                'unit_value': 50
            },
            {
                'name': 'Hybrid Rice Seeds IR64',
                'sku': 'SEED-RICE-IR64',
                'description': 'High-yielding hybrid rice variety',
                'category_id': categories[1].id,
                'supplier_id': suppliers[1].id,
                'cost_price': 120.00,
                'selling_price': 150.00,
                'stock_on_hand': 200,
                'reorder_point': 20,
                'uom': 'kg',
                'unit_value': 1
            },
            {
                'name': 'Urea Fertilizer 46-0-0',
                'sku': 'FERT-UREA-46',
                'description': 'High nitrogen content fertilizer',
                'category_id': categories[0].id,
                'supplier_id': suppliers[0].id,
                'cost_price': 1200.00,
                'selling_price': 1350.00,
                'stock_on_hand': 300,
                'reorder_point': 30,
                'uom': 'bag',
                'unit_value': 50
            },
            {
                'name': 'Insecticide Cypermethrin',
                'sku': 'PEST-CYPER-250',
                'description': 'Broad spectrum insecticide',
                'category_id': categories[2].id,
                'supplier_id': suppliers[2].id,
                'cost_price': 450.00,
                'selling_price': 520.00,
                'stock_on_hand': 150,
                'reorder_point': 15,
                'uom': 'liter',
                'unit_value': 1
            },
            {
                'name': 'Hand Tractor Plow',
                'sku': 'TOOL-PLOW-HT',
                'description': 'Heavy-duty plow for hand tractors',
                'category_id': categories[3].id,
                'supplier_id': suppliers[0].id,
                'cost_price': 8500.00,
                'selling_price': 9500.00,
                'stock_on_hand': 25,
                'reorder_point': 5,
                'uom': 'piece',
                'unit_value': 1
            }
        ]
        
        products = []
        for prod_data in products_data:
            product = Product(**prod_data)
            db.session.add(product)
            products.append(product)
        
        db.session.flush()
        print(f"✅ Created {len(products)} products")
        
        # 5. Create sample orders
        print("📦 Creating sample orders...")
        order_statuses = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
        payment_statuses = ['Pending', 'Paid', 'Partial', 'Failed']
        
        orders = []
        for i in range(12):
            farmer = random.choice(farmers)
            status = random.choice(order_statuses)
            payment_status = random.choice(payment_statuses)
            
            # Create order date within last 30 days
            days_ago = random.randint(0, 30)
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            order = Order(
                farmer_id=farmer.id,
                order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{i+1:03d}",
                status=status,
                payment_status=payment_status,
                notes=f"Sample order #{i+1} for {farmer.full_name}",
                delivery_address=f"{farmer.barangay}, Laguna, Philippines",
                created_by="System Admin",
                created_at=order_date,
                updated_at=order_date
            )
            
            # Add delivery date for shipped/delivered orders
            if status in ['Shipped', 'Delivered']:
                order.delivery_date = order_date + timedelta(days=random.randint(1, 7))
            
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Add 1-3 order items per order
            num_items = random.randint(1, 3)
            total_amount = 0
            
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product in selected_products:
                quantity = random.randint(1, 5)
                unit_price = float(product.selling_price)
                item_total = quantity * unit_price
                total_amount += item_total
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=item_total
                )
                db.session.add(order_item)
            
            # Update order total
            order.total_amount = total_amount
            orders.append(order)
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Created {len(orders)} sample orders")
        
        # Print comprehensive summary
        print("\n🎉 Sample Data Population Completed Successfully!")
        print("📊 Summary:")
        print(f"  • Farmers: {len(farmers)}")
        print(f"  • Categories: {len(categories)}")
        print(f"  • Suppliers: {len(suppliers)}")
        print(f"  • Products: {len(products)}")
        print(f"  • Orders: {len(orders)}")
        
        # Order status summary
        status_counts = {}
        for order in orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
        
        print("\n📦 Order Status Summary:")
        for status, count in status_counts.items():
            print(f"  • {status}: {count}")
        
        total_revenue = sum(order.total_amount for order in orders)
        print(f"\n💰 Total Sample Revenue: ₱{total_revenue:,.2f}")

if __name__ == "__main__":
    populate_all_sample_data()


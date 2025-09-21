#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import random
from src.models.user import db
from src.models.farmer import Farmer
from src.models.product import Product
from src.models.order import Order, OrderItem
from src.main import app

def populate_sample_orders():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Get existing farmers and products
        farmers = Farmer.query.all()
        products = Product.query.all()
        
        if not farmers:
            print("No farmers found. Please populate farmers first.")
            return
            
        if not products:
            print("No products found. Please populate products first.")
            return
        
        # Clear existing orders
        OrderItem.query.delete()
        Order.query.delete()
        
        # Sample order data
        order_statuses = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
        payment_statuses = ['Pending', 'Paid', 'Partial', 'Failed']
        
        sample_orders = []
        
        # Create 15 sample orders
        for i in range(15):
            farmer = random.choice(farmers)
            status = random.choice(order_statuses)
            payment_status = random.choice(payment_statuses)
            
            # Create order date within last 30 days
            days_ago = random.randint(0, 30)
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            order = Order(
                farmer_id=farmer.id,
                status=status,
                payment_status=payment_status,
                notes=f"Sample order #{i+1} for testing purposes",
                delivery_address=f"{farmer.barangay}, {farmer.municipality or 'Laguna'}, Philippines",
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
                quantity = random.randint(1, 10)
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
            sample_orders.append(order)
        
        # Commit all changes
        db.session.commit()
        
        print(f"Successfully created {len(sample_orders)} sample orders!")
        
        # Print summary
        status_counts = {}
        for order in sample_orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
        
        print("\nOrder Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        total_revenue = sum(order.total_amount for order in sample_orders)
        print(f"\nTotal Sample Revenue: ₱{total_revenue:,.2f}")

if __name__ == "__main__":
    populate_sample_orders()


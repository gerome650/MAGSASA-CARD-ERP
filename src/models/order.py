"""
Order Model for AgSense ERP
Comprehensive order management with farmer and product relationships
"""

from datetime import datetime
from .user import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending')
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)
    total_margin = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(50), default='Pending')
    notes = db.Column(db.Text)
    delivery_address = db.Column(db.Text)
    delivery_date = db.Column(db.DateTime)
    partner_id = db.Column(db.Integer, nullable=True)  # Removed foreign key constraint
    created_by = db.Column(db.String(100))  # CARD MRI officer name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farmer = db.relationship('Farmer', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    # Order status options
    STATUS_OPTIONS = [
        'Pending',
        'Approved',
        'Rejected',
        'Processing',
        'Shipped',
        'Delivered',
        'Canceled'
    ]

    # Payment status options
    PAYMENT_STATUS_OPTIONS = [
        'Pending',
        'Paid',
        'Failed',
        'Refunded'
    ]

    def __repr__(self):
        return f'<Order {self.order_number}: {self.farmer.name if self.farmer else "Unknown"}>'

    def to_dict(self):
        """Convert order to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'farmer_id': self.farmer_id,
            'farmer_name': self.farmer.name if self.farmer else None,
            'farmer_mobile': self.farmer.mobile if self.farmer else None,
            'farmer_barangay': self.farmer.barangay if self.farmer else None,
            'order_number': self.order_number,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'total_cost': self.total_cost,
            'total_margin': self.total_margin,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'delivery_address': self.delivery_address,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'partner_id': self.partner_id,
            'partner_name': None,  # Partner relationship removed
            'created_by': self.created_by,
            'item_count': len(self.order_items) if self.order_items else 0,
            'order_items': [item.to_dict() for item in self.order_items] if self.order_items else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_summary_dict(self):
        """Convert order to summary dictionary (without items)"""
        return {
            'id': self.id,
            'farmer_id': self.farmer_id,
            'farmer_name': self.farmer.name if self.farmer else None,
            'order_number': self.order_number,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'total_margin': self.total_margin,
            'payment_status': self.payment_status,
            'item_count': len(self.order_items) if self.order_items else 0,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def generate_order_number(cls):
        """Generate a unique order number"""
        import random
        import string

        # Format: AGS-YYYYMMDD-XXXX
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=4))
        order_number = f"AGS-{date_str}-{random_str}"

        # Check if order number already exists
        while cls.query.filter_by(order_number=order_number).first():
            random_str = ''.join(random.choices(string.digits, k=4))
            order_number = f"AGS-{date_str}-{random_str}"

        return order_number

    def calculate_totals(self):
        """Calculate and update totals from order items"""
        if self.order_items:
            self.total_amount = sum(item.total_price for item in self.order_items)
            self.total_cost = sum(item.total_cost for item in self.order_items)
            self.total_margin = self.total_amount - self.total_cost
        else:
            self.total_amount = 0.0
            self.total_cost = 0.0
            self.total_margin = 0.0
        return self.total_amount

    def update_status(self, new_status, notes=None):
        """Update order status with optional notes"""
        if new_status in self.STATUS_OPTIONS:
            self.status = new_status
            if notes:
                self.notes = notes
            self.updated_at = datetime.utcnow()
            return True
        return False

    @classmethod
    def get_by_farmer(cls, farmer_id):
        """Get all orders for a specific farmer"""
        return cls.query.filter_by(farmer_id=farmer_id).order_by(cls.order_date.desc()).all()

    @classmethod
    def get_by_status(cls, status):
        """Get all orders with a specific status"""
        return cls.query.filter_by(status=status).order_by(cls.order_date.desc()).all()

    @classmethod
    def get_recent_orders(cls, limit=10):
        """Get recent orders"""
        return cls.query.order_by(cls.order_date.desc()).limit(limit).all()

    def get_status_color(self):
        """Get color code for order status"""
        status_colors = {
            'Pending': '#f59e0b',      # yellow
            'Approved': '#10b981',     # green
            'Rejected': '#ef4444',     # red
            'Processing': '#3b82f6',   # blue
            'Shipped': '#8b5cf6',      # purple
            'Delivered': '#059669',    # emerald
            'Canceled': '#6b7280'      # gray
        }
        return status_colors.get(self.status, '#6b7280')


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    margin = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.id}: {self.quantity}x Product {self.product_id}>'

    def to_dict(self):
        """Convert order item to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'product_brand': self.product.brand if self.product else None,
            'product_uom': self.product.unit_of_measure if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'unit_cost': self.unit_cost,
            'total_price': self.total_price,
            'total_cost': self.total_cost,
            'margin': self.margin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create_from_cart_item(cls, order_id, cart_item, product):
        """Create an order item from a cart item and product"""
        unit_price = product.selling_price
        unit_cost = product.cost_price
        total_price = cart_item['quantity'] * unit_price
        total_cost = cart_item['quantity'] * unit_cost
        margin = total_price - total_cost

        return cls(
            order_id=order_id,
            product_id=cart_item['product_id'],
            quantity=cart_item['quantity'],
            unit_price=unit_price,
            unit_cost=unit_cost,
            total_price=total_price,
            total_cost=total_cost,
            margin=margin
        )

"""
Product Model for AgSense ERP Product Catalog
Comprehensive product management with inventory, pricing, and supplier integration
"""

from datetime import datetime
from .user import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    uom = db.Column(db.String(20), nullable=False)  # Unit of Measurement
    unit_value = db.Column(db.Numeric(10, 2))  # e.g., 50 for 50kg bag
    image_url = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))  # Path to thumbnail image
    image_filename = db.Column(db.String(200))  # Original filename for deletion
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Discontinued
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)  # Wholesale price from supplier
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)  # MRP for farmers
    stock_on_hand = db.Column(db.Integer, default=0)
    reorder_point = db.Column(db.Integer, default=10)

    # Additional product details
    composition = db.Column(db.Text)  # For fertilizers: NPK ratio, etc.
    application_rate = db.Column(db.String(100))  # Recommended application rate
    crop_suitability = db.Column(db.Text)  # Which crops this product is suitable for
    season_suitability = db.Column(db.String(100))  # Wet/Dry season suitability

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='products')
    supplier = db.relationship('Supplier', backref='products')

    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'

    def to_dict(self):
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'brand': self.brand,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_path': self.category.get_full_path() if self.category else None,
            'uom': self.uom,
            'unit_value': float(self.unit_value) if self.unit_value else None,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'image_filename': self.image_filename,
            'status': self.status,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'selling_price': float(self.selling_price) if self.selling_price else None,
            'margin': self.calculate_margin(),
            'margin_percentage': self.calculate_margin_percentage(),
            'stock_on_hand': self.stock_on_hand,
            'reorder_point': self.reorder_point,
            'stock_status': self.get_stock_status(),
            'composition': self.composition,
            'application_rate': self.application_rate,
            'crop_suitability': self.crop_suitability,
            'season_suitability': self.season_suitability,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_margin(self):
        """Calculate gross margin (selling price - cost price)"""
        if self.selling_price and self.cost_price:
            return float(self.selling_price - self.cost_price)
        return 0.0

    def calculate_margin_percentage(self):
        """Calculate margin percentage"""
        if self.selling_price and self.cost_price and self.selling_price > 0:
            margin = self.selling_price - self.cost_price
            return float((margin / self.selling_price) * 100)
        return 0.0

    def get_stock_status(self):
        """Get stock status based on current stock and reorder point"""
        if self.stock_on_hand <= 0:
            return 'Out of Stock'
        elif self.stock_on_hand <= self.reorder_point:
            return 'Low Stock'
        else:
            return 'In Stock'

    def update_stock(self, quantity_change, reason='Manual Adjustment'):
        """Update stock quantity with tracking"""
        old_stock = self.stock_on_hand
        self.stock_on_hand += quantity_change

        # Ensure stock doesn't go negative
        if self.stock_on_hand < 0:
            self.stock_on_hand = 0

        # Log stock movement (future enhancement)
        # StockMovement.log_movement(self.id, old_stock, self.stock_on_hand, reason)

        return self.stock_on_hand

    @classmethod
    def get_low_stock_products(cls):
        """Get products that are at or below reorder point"""
        return cls.query.filter(cls.stock_on_hand <= cls.reorder_point).all()

    @classmethod
    def get_by_category(cls, category_id):
        """Get products by category"""
        return cls.query.filter_by(category_id=category_id).all()

    @classmethod
    def get_by_supplier(cls, supplier_id):
        """Get products by supplier"""
        return cls.query.filter_by(supplier_id=supplier_id).all()

    @classmethod
    def search_products(cls, search_term):
        """Search products by name, SKU, or brand"""
        search_pattern = f"%{search_term}%"
        return cls.query.filter(
            db.or_(
                cls.name.ilike(search_pattern),
                cls.sku.ilike(search_pattern),
                cls.brand.ilike(search_pattern)
            )
        ).all()

"""
Order Item Model for AgSense ERP
Handles individual items within orders
"""

from datetime import datetime

from .user import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    order = db.relationship("Order", back_populates="order_items")
    product = db.relationship("Product", backref="order_items")

    def __repr__(self):
        return f"<OrderItem {self.id}: {self.quantity}x Product {self.product_id}>"

    def to_dict(self):
        """Convert order item to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "product_sku": self.product.sku if self.product else None,
            "product_brand": self.product.brand if self.product else None,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_from_cart_item(cls, order_id, cart_item):
        """Create an order item from a cart item"""
        return cls(
            order_id=order_id,
            product_id=cart_item["product_id"],
            quantity=cart_item["quantity"],
            unit_price=cart_item["unit_price"],
            total_price=cart_item["quantity"] * cart_item["unit_price"],
        )

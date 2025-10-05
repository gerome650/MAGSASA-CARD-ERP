"""
Supplier Model for AgSense ERP Product Catalog
Handles supplier information and relationships with products
"""

from datetime import datetime

from .user import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    website = db.Column(db.String(255))
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))  # e.g., "Net 30", "COD"
    status = db.Column(db.String(20), default="Active")  # Active, Inactive
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Supplier {self.name}>"

    def to_dict(self):
        """Convert supplier to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "website": self.website,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_active_suppliers(cls):
        """Get all active suppliers"""
        return cls.query.filter_by(status="Active").all()

    def get_product_count(self):
        """Get the number of products from this supplier"""
        from models.product import Product

        return Product.query.filter_by(supplier_id=self.id).count()

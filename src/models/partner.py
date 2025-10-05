from datetime import datetime

from src.models.user import db


class Partner(db.Model):
    __tablename__ = "partner"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    partner_type = db.Column(db.String(50), nullable=False)  # Supplier, Logistics
    category = db.Column(db.String(100))  # Fertilizers, Seeds, Last-Mile Delivery, etc.
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    website = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Active")  # Active, Inactive, Pending
    commission_rate = db.Column(db.Float, default=0.0)
    commission_type = db.Column(
        db.String(20), default="Percentage"
    )  # Percentage, Fixed
    payment_terms = db.Column(db.String(100))  # Net 30, Net 60, etc.
    geographic_coverage = db.Column(db.String(200))
    rating = db.Column(db.Float, default=0.0)  # 1-5 star rating
    total_orders = db.Column(db.Integer, default=0)
    successful_deliveries = db.Column(db.Integer, default=0)
    total_commission_earned = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "partner_type": self.partner_type,
            "category": self.category,
            "contact_person": self.contact_person,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "website": self.website,
            "status": self.status,
            "commission_rate": self.commission_rate,
            "commission_type": self.commission_type,
            "payment_terms": self.payment_terms,
            "geographic_coverage": self.geographic_coverage,
            "rating": self.rating,
            "total_orders": self.total_orders,
            "successful_deliveries": self.successful_deliveries,
            "total_commission_earned": self.total_commission_earned,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

from src.models.user import db
from datetime import datetime


class CommissionPayout(db.Model):
    __tablename__ = 'commission_payout'

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    order_id = db.Column(db.Integer)  # Removed foreign key reference
    amount = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, nullable=False)
    base_amount = db.Column(db.Float, nullable=False)
    payout_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Cancelled
    payment_method = db.Column(db.String(50))
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'partner_id': self.partner_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'commission_rate': self.commission_rate,
            'base_amount': self.base_amount,
            'payout_date': self.payout_date.isoformat() if self.payout_date else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

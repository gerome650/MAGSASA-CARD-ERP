from src.models.user import db
from datetime import datetime

class PartnerContract(db.Model):
    __tablename__ = 'partner_contract'
    
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    contract_title = db.Column(db.String(200), nullable=False)
    contract_file_path = db.Column(db.String(500))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Expired, Terminated
    contract_value = db.Column(db.Float)
    commission_rate = db.Column(db.Float)
    terms_and_conditions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'partner_id': self.partner_id,
            'contract_title': self.contract_title,
            'contract_file_path': self.contract_file_path,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'contract_value': self.contract_value,
            'commission_rate': self.commission_rate,
            'terms_and_conditions': self.terms_and_conditions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


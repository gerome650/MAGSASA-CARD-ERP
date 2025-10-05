#!/usr/bin/env python3
"""
Fix farmer model to match the actual database schema
"""

# Update the farmer model to match the enhanced database schema
farmer_model_content = '''from src.models.user import db
from datetime import datetime
import uuid

class Farmer(db.Model):
    __tablename__ = 'farmers'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Personal Information - matching enhanced schema
    full_name = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(60), nullable=True)
    last_name = db.Column(db.String(60), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    mobile_number = db.Column(db.String(20), nullable=True)
    government_id = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Farm Information - matching enhanced schema
    land_size_ha = db.Column(db.Float, nullable=True)
    crop_types = db.Column(db.Text, nullable=True)  # This matches the database
    land_tenure = db.Column(db.String(50), nullable=True)
    farming_experience = db.Column(db.Integer, nullable=True)

    # AgScore & Risk Assessment - matching enhanced schema
    agscore = db.Column(db.Integer, nullable=True)
    agscore_grade = db.Column(db.String(10), nullable=True)
    risk_factors = db.Column(db.Text, nullable=True)

    # Loan Management - matching enhanced schema
    loan_status = db.Column(db.String(50), default='None')
    loan_amount = db.Column(db.Float, nullable=True)

    # Additional fields from enhanced schema
    registration_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'mobile_number': self.mobile_number,
            'government_id': self.government_id,
            'address': self.address,
            'land_size_ha': self.land_size_ha,
            'crop_types': self.crop_types,
            'land_tenure': self.land_tenure,
            'farming_experience': self.farming_experience,
            'agscore': self.agscore,
            'agscore_grade': self.agscore_grade,
            'risk_factors': self.risk_factors,
            'loan_status': self.loan_status,
            'loan_amount': self.loan_amount,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Legacy compatibility
            'name': self.full_name,
            'location': self.address,
            'phone': self.mobile_number,
            'crop_type': self.crop_types.split(',')[0].strip() if self.crop_types else None
        }

    def get_agscore_grade(self):
        """Calculate AgScore grade based on score"""
        if not self.agscore:
            return 'Poor'

        if self.agscore >= 800:
            return 'Excellent'
        elif self.agscore >= 700:
            return 'Good'
        elif self.agscore >= 600:
            return 'Fair'
        else:
            return 'Poor'

    def update_agscore(self, score, risk_factors=None):
        """Update AgScore and related fields"""
        self.agscore = score
        self.agscore_grade = self.get_agscore_grade()
        self.risk_factors = risk_factors
        self.updated_at = datetime.utcnow()
'''

# Write the updated model
with open("src/models/farmer.py", "w") as f:
    f.write(farmer_model_content)

print("✅ Updated farmer model to match enhanced database schema")
print("🔧 Fixed field mappings and to_dict() method")

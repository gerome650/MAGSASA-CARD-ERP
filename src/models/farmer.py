from datetime import datetime

from src.models.user import db


class Farmer(db.Model):
    __tablename__ = "farmers"

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
    loan_status = db.Column(db.String(50), default="None")
    loan_amount = db.Column(db.Float, nullable=True)

    # Additional fields from enhanced schema
    registration_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        # Calculate AgScore grade if not set
        agscore_grade = self.agscore_grade or self.get_agscore_grade()

        return {
            "id": self.id,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "mobile_number": self.mobile_number,
            "government_id": self.government_id,
            "address": self.address,
            "land_size_ha": self.land_size_ha,
            "crop_types": self.crop_types,
            "land_tenure": self.land_tenure,
            "farming_experience": self.farming_experience,
            "agscore": self.agscore,
            "agscore_grade": agscore_grade,
            "risk_factors": self.risk_factors,
            "loan_status": self.loan_status,
            "loan_amount": self.loan_amount,
            "registration_date": (
                self.registration_date.isoformat() if self.registration_date else None
            ),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Frontend compatibility fields
            "name": self.full_name,  # Primary name field
            "location": self.address,  # Primary location field
            "phone": self.mobile_number,  # Primary phone field
            "crop_type": (
                self.crop_types.split(",")[0].strip() if self.crop_types else "N/A"
            ),
            "farm_size": self.land_size_ha,
            # Extract barangay from address
            "barangay": (
                self.address.split(",")[0]
                if self.address and "," in self.address
                else self.address
            ),
            "farm_location_text": self.address,  # Location text field
            "unique_id": str(self.id).zfill(4),  # Generate unique ID from ID
        }

    def get_agscore_grade(self):
        """Calculate AgScore grade based on score"""
        if not self.agscore:
            return "Poor"

        if self.agscore >= 800:
            return "Excellent"
        elif self.agscore >= 700:
            return "Good"
        elif self.agscore >= 600:
            return "Fair"
        else:
            return "Poor"

    def update_agscore(self, score, risk_factors=None):
        """Update AgScore and related fields"""
        self.agscore = score
        self.agscore_grade = self.get_agscore_grade()
        self.risk_factors = risk_factors
        self.updated_at = datetime.utcnow()

"""
Category Model for AgSense ERP Product Catalog
Handles product categorization and hierarchical category structure
"""

from datetime import datetime
from .user import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        """Convert category to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'parent_name': self.parent.name if self.parent else None,
            'subcategory_count': len(self.subcategories) if self.subcategories else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_main_categories(cls):
        """Get all top-level categories (no parent)"""
        return cls.query.filter_by(parent_id=None).all()
    
    @classmethod
    def get_subcategories(cls, parent_id):
        """Get all subcategories for a given parent category"""
        return cls.query.filter_by(parent_id=parent_id).all()
    
    def get_full_path(self):
        """Get the full category path (e.g., 'Fertilizer > NPK')"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


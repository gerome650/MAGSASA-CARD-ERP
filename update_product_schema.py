#!/usr/bin/env python3
"""
Update Product database schema to add image fields
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.database import db

def update_schema():
    """Update database schema to add image fields to products table"""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'thumbnail_url' not in columns:
                print("Adding thumbnail_url column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE products ADD COLUMN thumbnail_url VARCHAR(255)'))
                    conn.commit()
            
            if 'image_filename' not in columns:
                print("Adding image_filename column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE products ADD COLUMN image_filename VARCHAR(200)'))
                    conn.commit()
            
            print("Database schema updated successfully!")
            
        except Exception as e:
            print(f"Error updating schema: {e}")

if __name__ == '__main__':
    update_schema()


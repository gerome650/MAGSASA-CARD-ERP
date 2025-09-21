#!/usr/bin/env python3
"""
Initialize database with farmers table and sample data for payment functionality
"""

import sqlite3
import os
from datetime import datetime, timedelta

def initialize_farmer_database():
    """Create farmers table and populate with sample data"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'agsense.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create farmers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                mobile_number TEXT,
                email TEXT,
                address TEXT,
                crop_type TEXT DEFAULT 'Rice',
                land_size_hectares REAL DEFAULT 2.0,
                loan_amount REAL DEFAULT 45000.0,
                loan_status TEXT DEFAULT 'ACTIVE',
                agscore INTEGER DEFAULT 750,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create payments table for tracking payment history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER,
                payment_number INTEGER,
                amount REAL NOT NULL,
                due_date DATE,
                paid_date DATE,
                status TEXT DEFAULT 'SCHEDULED',
                payment_method TEXT DEFAULT 'online',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farmer_id) REFERENCES farmers (id)
            )
        ''')
        
        # Check if farmers already exist
        cursor.execute('SELECT COUNT(*) FROM farmers')
        farmer_count = cursor.fetchone()[0]
        
        if farmer_count == 0:
            # Insert sample farmers
            farmers_data = [
                ('Carlos Lopez', '+63 912 345 6789', 'carlos.lopez@email.com', 'Barangay San Jose, Cabanatuan City', 'Rice', 2.5, 45000.0, 'ACTIVE', 780),
                ('Maria Santos', '+63 917 234 5678', 'maria.santos@email.com', 'Barangay Santa Rosa, Nueva Ecija', 'Corn', 3.0, 60000.0, 'ACTIVE', 820),
                ('Juan dela Cruz', '+63 918 345 6789', 'juan.delacruz@email.com', 'Barangay Poblacion, Tarlac', 'Rice', 1.8, 35000.0, 'ACTIVE', 750),
                ('Ana Reyes', '+63 919 456 7890', 'ana.reyes@email.com', 'Barangay Maligaya, Pampanga', 'Vegetables', 1.2, 25000.0, 'ACTIVE', 690),
                ('Pedro Garcia', '+63 920 567 8901', 'pedro.garcia@email.com', 'Barangay Bagong Silang, Bulacan', 'Rice', 4.0, 80000.0, 'ACTIVE', 850)
            ]
            
            cursor.executemany('''
                INSERT INTO farmers (full_name, mobile_number, email, address, crop_type, land_size_hectares, loan_amount, loan_status, agscore)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', farmers_data)
            
            print(f"Inserted {len(farmers_data)} sample farmers")
        
        # Generate payment schedules for all farmers
        cursor.execute('SELECT id, loan_amount FROM farmers')
        farmers = cursor.fetchall()
        
        for farmer_id, loan_amount in farmers:
            # Check if payments already exist for this farmer
            cursor.execute('SELECT COUNT(*) FROM payments WHERE farmer_id = ?', (farmer_id,))
            payment_count = cursor.fetchone()[0]
            
            if payment_count == 0:
                # Generate 12-month payment schedule
                monthly_payment = loan_amount / 12
                start_date = datetime.now() - timedelta(days=120)  # Start 4 months ago
                
                payments_data = []
                for i in range(12):
                    payment_date = start_date + timedelta(days=30 * i)
                    
                    # First 4 payments are PAID, 5th is DUE_SOON, rest are SCHEDULED
                    if i < 4:
                        status = 'PAID'
                        paid_date = payment_date.strftime('%Y-%m-%d')
                    elif i == 4:
                        status = 'DUE_SOON'
                        paid_date = None
                    else:
                        status = 'SCHEDULED'
                        paid_date = None
                    
                    payments_data.append((
                        farmer_id,
                        i + 1,
                        monthly_payment,
                        payment_date.strftime('%Y-%m-%d'),
                        paid_date,
                        status
                    ))
                
                cursor.executemany('''
                    INSERT INTO payments (farmer_id, payment_number, amount, due_date, paid_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', payments_data)
                
                print(f"Generated payment schedule for farmer {farmer_id}")
        
        # Create users table if it doesn't exist (for authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'farmer',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if Carlos Lopez user exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('carloslopez',))
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Add Carlos Lopez as a user (password: farmer123)
            # Using a simple hash for demo - in production use proper password hashing
            import hashlib
            password_hash = hashlib.sha256('farmer123'.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, first_name, last_name, email, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('carloslopez', password_hash, 'Carlos', 'Lopez', 'carlos.lopez@email.com', 'farmer'))
            
            print("Created user account for Carlos Lopez")
        
        conn.commit()
        print("Database initialization completed successfully!")
        
        # Display summary
        cursor.execute('SELECT COUNT(*) FROM farmers')
        farmer_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM payments')
        payment_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        print(f"\nDatabase Summary:")
        print(f"  Farmers: {farmer_count}")
        print(f"  Payments: {payment_count}")
        print(f"  Users: {user_count}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == '__main__':
    success = initialize_farmer_database()
    if success:
        print("\n✅ Database initialization successful!")
        print("You can now test the farmer payment functionality.")
    else:
        print("\n❌ Database initialization failed!")

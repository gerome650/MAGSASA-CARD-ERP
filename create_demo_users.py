#!/usr/bin/env python3.11

import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_demo_users():
    """Create demo users for all roles"""
    
    # Connect to database
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    # Clear existing users
    cursor.execute('DELETE FROM users')
    
    # Demo users to create
    demo_users = [
        {
            'username': 'admin',
            'password': 'admin123',
            'first_name': 'Super',
            'last_name': 'Admin',
            'email': 'admin@magsasa-card.com',
            'role': 'super_admin'
        },
        {
            'username': 'manager1',
            'password': 'manager123',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria.santos@magsasa-card.com',
            'role': 'manager'
        },
        {
            'username': 'officer1',
            'password': 'officer123',
            'first_name': 'Juan',
            'last_name': 'Cruz',
            'email': 'juan.cruz@magsasa-card.com',
            'role': 'officer'
        },
        {
            'username': 'carloslopez',
            'password': 'farmer123',
            'first_name': 'Carlos',
            'last_name': 'Lopez',
            'email': 'carlos.lopez@email.com',
            'role': 'farmer'
        }
    ]
    
    # Insert demo users
    for user in demo_users:
        password_hash = hash_password(user['password'])
        cursor.execute('''
            INSERT INTO users (username, password_hash, first_name, last_name, email, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['username'],
            password_hash,
            user['first_name'],
            user['last_name'],
            user['email'],
            user['role'],
            True,
            datetime.now()
        ))
        print(f"✅ Created user: {user['username']} ({user['role']}) - Password: {user['password']}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n🎉 All demo users created successfully!")
    print("\n🔐 Login Credentials:")
    print("Super Admin: admin / admin123")
    print("Manager: manager1 / manager123") 
    print("Officer: officer1 / officer123")
    print("Farmer: carloslopez / farmer123")

if __name__ == "__main__":
    create_demo_users()

#!/usr/bin/env python3
"""
Phase 2 Implementation: Farmer User Role and Authentication
Creates farmer role, permissions, and demo users for the MAGSASA-CARD ERP system
"""

import sqlite3
import hashlib
from datetime import datetime
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_farmer_role_and_users():
    """Create farmer role, permissions, and demo users"""
    
    # Database path
    db_path = '/home/ubuntu/agsense_erp/src/agsense.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Starting Phase 2: Farmer Role Implementation...")
        
        # 1. Create Farmer role if it doesn't exist
        print("\n📋 Step 1: Creating Farmer role...")
        cursor.execute("""
            INSERT OR IGNORE INTO roles (name, description, created_at)
            VALUES (?, ?, ?)
        """, ('Farmer', 'Individual farmer with access to personal loan and agricultural information', datetime.now()))
        
        # Get the farmer role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'Farmer'")
        farmer_role = cursor.fetchone()
        if farmer_role:
            farmer_role_id = farmer_role[0]
            print(f"✅ Farmer role created/found with ID: {farmer_role_id}")
        else:
            print("❌ Failed to create/find Farmer role")
            return False
        
        # 2. Define farmer-specific permissions
        print("\n🔐 Step 2: Setting up Farmer permissions...")
        farmer_permissions = [
            # Personal data access
            ('farmers', 'read', 'View personal farmer profile'),
            ('farmers', 'update', 'Update personal farmer information'),
            
            # Loan information access
            ('loans', 'read', 'View personal loan information'),
            ('loan_applications', 'read', 'View personal loan applications'),
            ('loan_applications', 'create', 'Submit new loan applications'),
            
            # Payment information
            ('payments', 'read', 'View personal payment history'),
            ('payment_schedules', 'read', 'View payment schedules'),
            
            # Agricultural advisory
            ('agricultural_tips', 'read', 'Access agricultural advice and tips'),
            ('weather_alerts', 'read', 'Receive weather alerts'),
            
            # Basic system access
            ('dashboard', 'read', 'Access farmer dashboard'),
            ('profile', 'read', 'View personal profile'),
            ('profile', 'update', 'Update personal profile'),
            
            # Notifications
            ('notifications', 'read', 'View personal notifications'),
            ('notifications', 'update', 'Mark notifications as read'),
        ]
        
        # Add permissions to database
        for module, action, description in farmer_permissions:
            cursor.execute("""
                INSERT OR IGNORE INTO permissions (module, action, description)
                VALUES (?, ?, ?)
            """, (module, action, description))
        
        # 3. Assign permissions to Farmer role
        print("\n🔗 Step 3: Assigning permissions to Farmer role...")
        for module, action, description in farmer_permissions:
            # Get permission ID
            cursor.execute("""
                SELECT id FROM permissions WHERE module = ? AND action = ?
            """, (module, action))
            permission = cursor.fetchone()
            
            if permission:
                permission_id = permission[0]
                # Assign permission to farmer role
                cursor.execute("""
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                """, (farmer_role_id, permission_id))
        
        print(f"✅ Assigned {len(farmer_permissions)} permissions to Farmer role")
        
        # 4. Create demo farmer users
        print("\n👨‍🌾 Step 4: Creating demo farmer users...")
        
        # Get existing farmers from the farmers table to link with user accounts
        cursor.execute("SELECT id, full_name, mobile_number FROM farmers LIMIT 5")
        existing_farmers = cursor.fetchall()
        
        demo_farmers = []
        for i, (farmer_id, farmer_name, mobile) in enumerate(existing_farmers):
            # Create username from farmer name (simplified)
            username = farmer_name.lower().replace(' ', '').replace('.', '')[:15]
            if len(username) < 5:
                username = f"farmer{i+1}"
            
            demo_farmers.append({
                'username': username,
                'password': 'farmer123',
                'email': f"{username}@farmer.magsasa.ph",
                'full_name': farmer_name,
                'farmer_id': farmer_id,
                'mobile': mobile
            })
        
        # Add additional demo farmers if we don't have enough
        if len(demo_farmers) < 3:
            additional_farmers = [
                {
                    'username': 'maria_santos',
                    'password': 'farmer123',
                    'email': 'maria.santos@farmer.magsasa.ph',
                    'full_name': 'Maria Santos',
                    'farmer_id': None,
                    'mobile': '09171234567'
                },
                {
                    'username': 'juan_cruz',
                    'password': 'farmer123',
                    'email': 'juan.cruz@farmer.magsasa.ph',
                    'full_name': 'Juan Dela Cruz',
                    'farmer_id': None,
                    'mobile': '09181234567'
                },
                {
                    'username': 'ana_reyes',
                    'password': 'farmer123',
                    'email': 'ana.reyes@farmer.magsasa.ph',
                    'full_name': 'Ana Reyes',
                    'farmer_id': None,
                    'mobile': '09191234567'
                }
            ]
            demo_farmers.extend(additional_farmers[:3-len(demo_farmers)])
        
        # Create user accounts for farmers
        created_users = 0
        for farmer_data in demo_farmers[:5]:  # Limit to 5 demo farmers
            try:
                # Split full name into first and last name
                name_parts = farmer_data['full_name'].split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                cursor.execute("""
                    INSERT OR IGNORE INTO users (
                        username, password_hash, email, first_name, last_name,
                        role_id, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    farmer_data['username'],
                    hash_password(farmer_data['password']),
                    farmer_data['email'],
                    first_name,
                    last_name,
                    farmer_role_id,
                    1,  # is_active
                    datetime.now()
                ))
                
                if cursor.rowcount > 0:
                    created_users += 1
                    print(f"✅ Created farmer user: {farmer_data['username']} ({farmer_data['full_name']})")
                
            except sqlite3.IntegrityError as e:
                print(f"⚠️  User {farmer_data['username']} already exists")
        
        print(f"✅ Created {created_users} new farmer user accounts")
        
        # 5. Update login page demo credentials
        print("\n🔧 Step 5: Updating login page with farmer demo credentials...")
        
        # Commit all changes
        conn.commit()
        
        # 6. Summary
        print("\n🎉 Phase 2 Step 1 Complete!")
        print("=" * 50)
        print(f"✅ Farmer role created with {len(farmer_permissions)} permissions")
        print(f"✅ {created_users} demo farmer accounts created")
        print("\n👨‍🌾 Demo Farmer Credentials:")
        for farmer_data in demo_farmers[:created_users]:
            print(f"   • Username: {farmer_data['username']} | Password: {farmer_data['password']}")
        
        print("\n🚀 Next Steps:")
        print("   1. Update login page with farmer demo credentials")
        print("   2. Create farmer dashboard route")
        print("   3. Implement farmer-specific dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Error implementing farmer role: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = create_farmer_role_and_users()
    if success:
        print("\n✅ Farmer role implementation completed successfully!")
    else:
        print("\n❌ Farmer role implementation failed!")


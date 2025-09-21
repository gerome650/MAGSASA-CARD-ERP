#!/usr/bin/env python3
"""
MAGSASA-CARD ERP - Phase 1 User Roles Implementation
Implements Super Admin, CARD MRI Officer, and CARD MRI Manager roles
"""

import sys
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_tables_and_data():
    """Create tables and insert data directly using SQLite"""
    
    db_path = '/home/ubuntu/agsense_erp/src/agsense.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                module VARCHAR(50) NOT NULL,
                action VARCHAR(20) NOT NULL,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER,
                permission_id INTEGER,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role_id INTEGER NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')
        
        # Insert permissions
        permissions = [
            # Farmer Management Permissions
            ('farmer_create', 'farmers', 'CREATE', 'Create new farmer profiles'),
            ('farmer_read', 'farmers', 'READ', 'View farmer profiles'),
            ('farmer_update', 'farmers', 'UPDATE', 'Update farmer profiles'),
            ('farmer_delete', 'farmers', 'DELETE', 'Delete farmer profiles'),
            ('farmer_read_all', 'farmers', 'READ', 'View all farmer profiles'),
            ('farmer_read_assigned', 'farmers', 'READ', 'View assigned farmer profiles'),
            
            # Product Management Permissions
            ('product_create', 'products', 'CREATE', 'Create new products'),
            ('product_read', 'products', 'READ', 'View products'),
            ('product_update', 'products', 'UPDATE', 'Update products'),
            ('product_delete', 'products', 'DELETE', 'Delete products'),
            
            # Order Management Permissions
            ('order_create', 'orders', 'CREATE', 'Create new orders'),
            ('order_read', 'orders', 'READ', 'View orders'),
            ('order_update', 'orders', 'UPDATE', 'Update orders'),
            ('order_delete', 'orders', 'DELETE', 'Delete orders'),
            ('order_approve', 'orders', 'UPDATE', 'Approve orders'),
            ('order_read_all', 'orders', 'READ', 'View all orders'),
            ('order_read_assigned', 'orders', 'READ', 'View assigned orders'),
            
            # Partner Management Permissions
            ('partner_create', 'partners', 'CREATE', 'Create new partners'),
            ('partner_read', 'partners', 'READ', 'View partners'),
            ('partner_update', 'partners', 'UPDATE', 'Update partners'),
            ('partner_delete', 'partners', 'DELETE', 'Delete partners'),
            
            # Financial Permissions
            ('financial_read', 'financial', 'READ', 'View financial reports'),
            ('financial_read_all', 'financial', 'READ', 'View all financial data'),
            ('financial_read_assigned', 'financial', 'READ', 'View assigned financial data'),
            
            # Loan Management Permissions
            ('loan_create', 'loans', 'CREATE', 'Create loan applications'),
            ('loan_read', 'loans', 'READ', 'View loan applications'),
            ('loan_update', 'loans', 'UPDATE', 'Update loan applications'),
            ('loan_approve', 'loans', 'UPDATE', 'Approve loan applications'),
            ('loan_reject', 'loans', 'UPDATE', 'Reject loan applications'),
            ('loan_disburse', 'loans', 'UPDATE', 'Disburse approved loans'),
            
            # Reporting Permissions
            ('report_read', 'reports', 'READ', 'View reports'),
            ('report_create', 'reports', 'CREATE', 'Create reports'),
            ('report_export', 'reports', 'READ', 'Export reports'),
            ('report_read_all', 'reports', 'READ', 'View all reports'),
            ('report_read_assigned', 'reports', 'READ', 'View assigned reports'),
            
            # User Management Permissions
            ('user_create', 'users', 'CREATE', 'Create new users'),
            ('user_read', 'users', 'READ', 'View users'),
            ('user_update', 'users', 'UPDATE', 'Update users'),
            ('user_delete', 'users', 'DELETE', 'Delete users'),
            ('user_manage_roles', 'users', 'UPDATE', 'Manage user roles'),
            
            # System Administration Permissions
            ('system_admin', 'system', 'UPDATE', 'System administration'),
            ('system_backup', 'system', 'CREATE', 'Create system backups'),
            ('system_restore', 'system', 'UPDATE', 'Restore system backups'),
            ('system_logs', 'system', 'READ', 'View system logs'),
            
            # AgScore and Assessment Permissions
            ('agscore_read', 'agscore', 'READ', 'View AgScore assessments'),
            ('agscore_update', 'agscore', 'UPDATE', 'Update AgScore assessments'),
            ('agscore_calculate', 'agscore', 'CREATE', 'Calculate AgScore'),
            
            # Field Operations Permissions
            ('field_visit_create', 'field', 'CREATE', 'Log field visits'),
            ('field_visit_read', 'field', 'READ', 'View field visits'),
            ('field_visit_update', 'field', 'UPDATE', 'Update field visits'),
            ('field_data_update', 'field', 'UPDATE', 'Update field data'),
        ]
        
        for perm in permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (name, module, action, description)
                VALUES (?, ?, ?, ?)
            ''', perm)
        
        # Insert roles
        roles = [
            ('Super Admin', 'Full system access with all administrative privileges'),
            ('CARD MRI Manager', 'Branch/Regional manager with oversight and approval capabilities'),
            ('CARD MRI Officer', 'Loan officer with farmer management and loan processing capabilities')
        ]
        
        for role in roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (name, description)
                VALUES (?, ?)
            ''', role)
        
        # Get role IDs
        cursor.execute('SELECT id, name FROM roles')
        role_map = {name: id for id, name in cursor.fetchall()}
        
        # Get permission IDs
        cursor.execute('SELECT id, name FROM permissions')
        perm_map = {name: id for id, name in cursor.fetchall()}
        
        # Define role permissions
        role_permissions = {
            'Super Admin': list(perm_map.keys()),  # All permissions
            'CARD MRI Manager': [
                'farmer_create', 'farmer_read', 'farmer_update', 'farmer_read_all',
                'product_read',
                'order_create', 'order_read', 'order_update', 'order_approve', 'order_read_all',
                'partner_read', 'partner_update',
                'financial_read', 'financial_read_assigned',
                'loan_read', 'loan_update', 'loan_approve', 'loan_reject', 'loan_disburse',
                'report_read', 'report_create', 'report_export', 'report_read_all',
                'user_read', 'user_update',
                'agscore_read', 'agscore_update', 'agscore_calculate',
                'field_visit_read', 'field_visit_update', 'field_data_update'
            ],
            'CARD MRI Officer': [
                'farmer_create', 'farmer_read', 'farmer_update', 'farmer_read_assigned',
                'product_read',
                'order_create', 'order_read', 'order_update', 'order_read_assigned',
                'partner_read',
                'financial_read_assigned',
                'loan_create', 'loan_read', 'loan_update',
                'report_read', 'report_read_assigned', 'report_export',
                'agscore_read', 'agscore_update', 'agscore_calculate',
                'field_visit_create', 'field_visit_read', 'field_visit_update', 'field_data_update'
            ]
        }
        
        # Clear existing role permissions and insert new ones
        cursor.execute('DELETE FROM role_permissions')
        
        for role_name, permissions in role_permissions.items():
            role_id = role_map[role_name]
            for perm_name in permissions:
                if perm_name in perm_map:
                    cursor.execute('''
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    ''', (role_id, perm_map[perm_name]))
        
        # Create demo users
        demo_users = [
            ('admin', 'admin@magsasa-card.org', 'admin123', 'System', 'Administrator', 'Super Admin'),
            ('manager1', 'manager1@magsasa-card.org', 'manager123', 'Maria', 'Santos', 'CARD MRI Manager'),
            ('manager2', 'manager2@magsasa-card.org', 'manager123', 'Juan', 'Dela Cruz', 'CARD MRI Manager'),
            ('officer1', 'officer1@magsasa-card.org', 'officer123', 'Ana', 'Reyes', 'CARD MRI Officer'),
            ('officer2', 'officer2@magsasa-card.org', 'officer123', 'Carlos', 'Garcia', 'CARD MRI Officer'),
            ('officer3', 'officer3@magsasa-card.org', 'officer123', 'Rosa', 'Mendoza', 'CARD MRI Officer'),
        ]
        
        for username, email, password, first_name, last_name, role_name in demo_users:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            role_id = role_map[role_name]
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (username, email, password_hash, first_name, last_name, role_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ''', (username, email, password_hash, first_name, last_name, role_id, datetime.utcnow().isoformat()))
        
        conn.commit()
        
        # Get counts for summary
        cursor.execute('SELECT COUNT(*) FROM permissions')
        perm_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM roles')
        role_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        print("✅ Phase 1 Implementation Complete!")
        print("\n📊 Summary:")
        print(f"   • Permissions: {perm_count} created/verified")
        print(f"   • Roles: {role_count} created/updated")
        print(f"   • Users: {user_count} created/updated")
        
        print("\n🔐 Demo Login Credentials:")
        print("   Super Admin:")
        print("     Username: admin | Password: admin123")
        print("   CARD MRI Manager:")
        print("     Username: manager1 | Password: manager123")
        print("     Username: manager2 | Password: manager123")
        print("   CARD MRI Officer:")
        print("     Username: officer1 | Password: officer123")
        print("     Username: officer2 | Password: officer123")
        print("     Username: officer3 | Password: officer123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during implementation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def main():
    """Main implementation function"""
    print("🚀 Starting Phase 1 User Roles Implementation...")
    print("=" * 60)
    
    success = create_tables_and_data()
    
    if success:
        print("\n🎯 Next Steps:")
        print("   1. Test login with different user roles")
        print("   2. Verify role-based access controls")
        print("   3. Create role-specific dashboards")
        print("   4. Implement permission-based navigation")
        print("\n🎉 Phase 1 User Roles Implementation Successful!")
    else:
        print("\n💥 Phase 1 Implementation Failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)


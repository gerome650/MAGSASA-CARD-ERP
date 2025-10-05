#!/usr/bin/env python3
"""
Initialize Authentication System
This script sets up the initial roles and permissions for the AgSense ERP system.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.database import db
from src.main import app
from src.models.user import Permission, Role, RolePermission, User


def initialize_permissions():
    """Create all permissions for the system"""
    permissions_data = [
        # User Management
        {
            "name": "user_management_create",
            "module": "user_management",
            "action": "CREATE",
            "description": "Create new users",
        },
        {
            "name": "user_management_read",
            "module": "user_management",
            "action": "READ",
            "description": "View users and roles",
        },
        {
            "name": "user_management_update",
            "module": "user_management",
            "action": "UPDATE",
            "description": "Update user information",
        },
        {
            "name": "user_management_delete",
            "module": "user_management",
            "action": "DELETE",
            "description": "Delete users",
        },
        # Farmer Management
        {
            "name": "farmer_create",
            "module": "farmer",
            "action": "CREATE",
            "description": "Add new farmers",
        },
        {
            "name": "farmer_read",
            "module": "farmer",
            "action": "READ",
            "description": "View farmer information",
        },
        {
            "name": "farmer_update",
            "module": "farmer",
            "action": "UPDATE",
            "description": "Update farmer information",
        },
        {
            "name": "farmer_delete",
            "module": "farmer",
            "action": "DELETE",
            "description": "Delete farmers",
        },
        {
            "name": "farmer_export",
            "module": "farmer",
            "action": "READ",
            "description": "Export farmer data",
        },
        # Product Management
        {
            "name": "product_create",
            "module": "product",
            "action": "CREATE",
            "description": "Add new products",
        },
        {
            "name": "product_read",
            "module": "product",
            "action": "READ",
            "description": "View product catalog",
        },
        {
            "name": "product_update",
            "module": "product",
            "action": "UPDATE",
            "description": "Update product information",
        },
        {
            "name": "product_delete",
            "module": "product",
            "action": "DELETE",
            "description": "Delete products",
        },
        {
            "name": "inventory_manage",
            "module": "product",
            "action": "UPDATE",
            "description": "Manage inventory levels",
        },
        # Order Management
        {
            "name": "order_create",
            "module": "order",
            "action": "CREATE",
            "description": "Create new orders",
        },
        {
            "name": "order_read",
            "module": "order",
            "action": "READ",
            "description": "View orders",
        },
        {
            "name": "order_update",
            "module": "order",
            "action": "UPDATE",
            "description": "Update order status",
        },
        {
            "name": "order_delete",
            "module": "order",
            "action": "DELETE",
            "description": "Cancel/delete orders",
        },
        {
            "name": "order_approve",
            "module": "order",
            "action": "UPDATE",
            "description": "Approve orders",
        },
        # Partnership Management
        {
            "name": "partner_create",
            "module": "partner",
            "action": "CREATE",
            "description": "Add new partners",
        },
        {
            "name": "partner_read",
            "module": "partner",
            "action": "READ",
            "description": "View partner information",
        },
        {
            "name": "partner_update",
            "module": "partner",
            "action": "UPDATE",
            "description": "Update partner information",
        },
        {
            "name": "partner_delete",
            "module": "partner",
            "action": "DELETE",
            "description": "Remove partners",
        },
        {
            "name": "commission_manage",
            "module": "partner",
            "action": "UPDATE",
            "description": "Manage commission payouts",
        },
        # Financial Reports
        {
            "name": "financial_read",
            "module": "financial",
            "action": "READ",
            "description": "View financial reports",
        },
        {
            "name": "financial_export",
            "module": "financial",
            "action": "READ",
            "description": "Export financial data",
        },
        {
            "name": "financial_advanced",
            "module": "financial",
            "action": "READ",
            "description": "Access advanced financial analytics",
        },
        # Analytics
        {
            "name": "analytics_read",
            "module": "analytics",
            "action": "READ",
            "description": "View analytics dashboards",
        },
        {
            "name": "analytics_export",
            "module": "analytics",
            "action": "READ",
            "description": "Export analytics data",
        },
        # Dashboard
        {
            "name": "dashboard_read",
            "module": "dashboard",
            "action": "READ",
            "description": "View dashboard",
        },
        # System Administration
        {
            "name": "system_admin",
            "module": "system",
            "action": "UPDATE",
            "description": "Full system administration access",
        },
    ]

    for perm_data in permissions_data:
        existing = Permission.query.filter_by(name=perm_data["name"]).first()
        if not existing:
            permission = Permission(**perm_data)
            db.session.add(permission)

    db.session.commit()
    print(f"✓ Initialized {len(permissions_data)} permissions")


def initialize_roles():
    """Create all roles for the system"""
    roles_data = [
        {
            "name": "super_admin",
            "description": "Full system access with all permissions",
            "permissions": [
                "user_management_create",
                "user_management_read",
                "user_management_update",
                "user_management_delete",
                "farmer_create",
                "farmer_read",
                "farmer_update",
                "farmer_delete",
                "farmer_export",
                "product_create",
                "product_read",
                "product_update",
                "product_delete",
                "inventory_manage",
                "order_create",
                "order_read",
                "order_update",
                "order_delete",
                "order_approve",
                "partner_create",
                "partner_read",
                "partner_update",
                "partner_delete",
                "commission_manage",
                "financial_read",
                "financial_export",
                "financial_advanced",
                "analytics_read",
                "analytics_export",
                "dashboard_read",
                "system_admin",
            ],
        },
        {
            "name": "agsense_management",
            "description": "AgSense management team with comprehensive access",
            "permissions": [
                "farmer_create",
                "farmer_read",
                "farmer_update",
                "farmer_export",
                "product_create",
                "product_read",
                "product_update",
                "inventory_manage",
                "order_create",
                "order_read",
                "order_update",
                "order_approve",
                "partner_create",
                "partner_read",
                "partner_update",
                "commission_manage",
                "financial_read",
                "financial_export",
                "financial_advanced",
                "analytics_read",
                "analytics_export",
                "dashboard_read",
            ],
        },
        {
            "name": "card_mri_management",
            "description": "CARD MRI management team with farmer and financial focus",
            "permissions": [
                "farmer_read",
                "farmer_update",
                "farmer_export",
                "product_read",
                "order_read",
                "order_update",
                "partner_read",
                "financial_read",
                "financial_export",
                "analytics_read",
                "dashboard_read",
            ],
        },
        {
            "name": "agsense_operations",
            "description": "AgSense operations team for day-to-day activities",
            "permissions": [
                "farmer_create",
                "farmer_read",
                "farmer_update",
                "product_read",
                "product_update",
                "inventory_manage",
                "order_create",
                "order_read",
                "order_update",
                "partner_read",
                "partner_update",
                "analytics_read",
                "dashboard_read",
            ],
        },
        {
            "name": "card_mri_field_officer",
            "description": "CARD MRI field officers with limited farmer access",
            "permissions": [
                "farmer_read",
                "farmer_update",
                "product_read",
                "order_read",
                "dashboard_read",
            ],
        },
    ]

    for role_data in roles_data:
        existing_role = Role.query.filter_by(name=role_data["name"]).first()
        if not existing_role:
            role = Role(name=role_data["name"], description=role_data["description"])
            db.session.add(role)
            db.session.flush()  # Get the role ID

            # Add permissions to role
            for perm_name in role_data["permissions"]:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission(
                        role_id=role.id, permission_id=permission.id
                    )
                    db.session.add(role_permission)

    db.session.commit()
    print(f"✓ Initialized {len(roles_data)} roles")


def create_default_admin():
    """Create a default super admin user"""
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        super_admin_role = Role.query.filter_by(name="super_admin").first()
        if super_admin_role:
            admin = User(
                username="admin",
                email="admin@agsense.com",
                first_name="System",
                last_name="Administrator",
                role_id=super_admin_role.id,
                is_active=True,
            )
            admin.set_password("admin123")  # Default password - should be changed
            db.session.add(admin)
            db.session.commit()
            print("✓ Created default admin user (username: admin, password: admin123)")
        else:
            print("✗ Could not create admin user - super_admin role not found")
    else:
        print("✓ Admin user already exists")


def create_sample_users():
    """Create sample users for each role"""
    sample_users = [
        {
            "username": "agsense_mgr",
            "email": "manager@agsense.com",
            "first_name": "AgSense",
            "last_name": "Manager",
            "role": "agsense_management",
            "password": "agsense123",
        },
        {
            "username": "card_mgr",
            "email": "manager@cardmri.com",
            "first_name": "CARD MRI",
            "last_name": "Manager",
            "role": "card_mri_management",
            "password": "cardmri123",
        },
        {
            "username": "agsense_ops",
            "email": "operations@agsense.com",
            "first_name": "AgSense",
            "last_name": "Operations",
            "role": "agsense_operations",
            "password": "operations123",
        },
        {
            "username": "field_officer",
            "email": "field@cardmri.com",
            "first_name": "Field",
            "last_name": "Officer",
            "role": "card_mri_field_officer",
            "password": "field123",
        },
    ]

    created_count = 0
    for user_data in sample_users:
        existing_user = User.query.filter_by(username=user_data["username"]).first()
        if not existing_user:
            role = Role.query.filter_by(name=user_data["role"]).first()
            if role:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role_id=role.id,
                    is_active=True,
                )
                user.set_password(user_data["password"])
                db.session.add(user)
                created_count += 1

    db.session.commit()
    print(f"✓ Created {created_count} sample users")


def main():
    """Initialize the complete authentication system"""
    print("Initializing AgSense ERP Authentication System...")
    print("=" * 50)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Initialize permissions
        initialize_permissions()

        # Initialize roles
        initialize_roles()

        # Create default admin user
        create_default_admin()

        # Create sample users
        create_sample_users()

        print("=" * 50)
        print("Authentication system initialized successfully!")
        print("\nDefault Login Credentials:")
        print("- Super Admin: admin / admin123")
        print("- AgSense Manager: agsense_mgr / agsense123")
        print("- CARD MRI Manager: card_mgr / cardmri123")
        print("- AgSense Operations: agsense_ops / operations123")
        print("- Field Officer: field_officer / field123")
        print("\n⚠️  Please change default passwords after first login!")


if __name__ == "__main__":
    main()

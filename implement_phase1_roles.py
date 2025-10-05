#!/usr/bin/env python3
"""
MAGSASA-CARD ERP - Phase 1 User Roles Implementation
Implements Super Admin, CARD MRI Officer, and CARD MRI Manager roles
"""

import os
import sys

sys.path.append("/home/ubuntu/agsense_erp/src")

from datetime import datetime

from flask import Flask

from database import db
from models.user import Permission, Role, RolePermission, User


def init_app():
    """Initialize Flask app and database"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join('/home/ubuntu/agsense_erp/src', 'agsense.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        return app


def create_permissions():
    """Create all necessary permissions for the system"""
    permissions = [
        # Farmer Management Permissions
        {
            "name": "farmer_create",
            "module": "farmers",
            "action": "CREATE",
            "description": "Create new farmer profiles",
        },
        {
            "name": "farmer_read",
            "module": "farmers",
            "action": "READ",
            "description": "View farmer profiles",
        },
        {
            "name": "farmer_update",
            "module": "farmers",
            "action": "UPDATE",
            "description": "Update farmer profiles",
        },
        {
            "name": "farmer_delete",
            "module": "farmers",
            "action": "DELETE",
            "description": "Delete farmer profiles",
        },
        {
            "name": "farmer_read_all",
            "module": "farmers",
            "action": "READ",
            "description": "View all farmer profiles",
        },
        {
            "name": "farmer_read_assigned",
            "module": "farmers",
            "action": "READ",
            "description": "View assigned farmer profiles",
        },
        # Product Management Permissions
        {
            "name": "product_create",
            "module": "products",
            "action": "CREATE",
            "description": "Create new products",
        },
        {
            "name": "product_read",
            "module": "products",
            "action": "READ",
            "description": "View products",
        },
        {
            "name": "product_update",
            "module": "products",
            "action": "UPDATE",
            "description": "Update products",
        },
        {
            "name": "product_delete",
            "module": "products",
            "action": "DELETE",
            "description": "Delete products",
        },
        # Order Management Permissions
        {
            "name": "order_create",
            "module": "orders",
            "action": "CREATE",
            "description": "Create new orders",
        },
        {
            "name": "order_read",
            "module": "orders",
            "action": "READ",
            "description": "View orders",
        },
        {
            "name": "order_update",
            "module": "orders",
            "action": "UPDATE",
            "description": "Update orders",
        },
        {
            "name": "order_delete",
            "module": "orders",
            "action": "DELETE",
            "description": "Delete orders",
        },
        {
            "name": "order_approve",
            "module": "orders",
            "action": "UPDATE",
            "description": "Approve orders",
        },
        {
            "name": "order_read_all",
            "module": "orders",
            "action": "READ",
            "description": "View all orders",
        },
        {
            "name": "order_read_assigned",
            "module": "orders",
            "action": "READ",
            "description": "View assigned orders",
        },
        # Partner Management Permissions
        {
            "name": "partner_create",
            "module": "partners",
            "action": "CREATE",
            "description": "Create new partners",
        },
        {
            "name": "partner_read",
            "module": "partners",
            "action": "READ",
            "description": "View partners",
        },
        {
            "name": "partner_update",
            "module": "partners",
            "action": "UPDATE",
            "description": "Update partners",
        },
        {
            "name": "partner_delete",
            "module": "partners",
            "action": "DELETE",
            "description": "Delete partners",
        },
        # Financial Permissions
        {
            "name": "financial_read",
            "module": "financial",
            "action": "READ",
            "description": "View financial reports",
        },
        {
            "name": "financial_read_all",
            "module": "financial",
            "action": "READ",
            "description": "View all financial data",
        },
        {
            "name": "financial_read_assigned",
            "module": "financial",
            "action": "READ",
            "description": "View assigned financial data",
        },
        # Loan Management Permissions
        {
            "name": "loan_create",
            "module": "loans",
            "action": "CREATE",
            "description": "Create loan applications",
        },
        {
            "name": "loan_read",
            "module": "loans",
            "action": "READ",
            "description": "View loan applications",
        },
        {
            "name": "loan_update",
            "module": "loans",
            "action": "UPDATE",
            "description": "Update loan applications",
        },
        {
            "name": "loan_approve",
            "module": "loans",
            "action": "UPDATE",
            "description": "Approve loan applications",
        },
        {
            "name": "loan_reject",
            "module": "loans",
            "action": "UPDATE",
            "description": "Reject loan applications",
        },
        {
            "name": "loan_disburse",
            "module": "loans",
            "action": "UPDATE",
            "description": "Disburse approved loans",
        },
        # Reporting Permissions
        {
            "name": "report_read",
            "module": "reports",
            "action": "READ",
            "description": "View reports",
        },
        {
            "name": "report_create",
            "module": "reports",
            "action": "CREATE",
            "description": "Create reports",
        },
        {
            "name": "report_export",
            "module": "reports",
            "action": "READ",
            "description": "Export reports",
        },
        {
            "name": "report_read_all",
            "module": "reports",
            "action": "READ",
            "description": "View all reports",
        },
        {
            "name": "report_read_assigned",
            "module": "reports",
            "action": "READ",
            "description": "View assigned reports",
        },
        # User Management Permissions
        {
            "name": "user_create",
            "module": "users",
            "action": "CREATE",
            "description": "Create new users",
        },
        {
            "name": "user_read",
            "module": "users",
            "action": "READ",
            "description": "View users",
        },
        {
            "name": "user_update",
            "module": "users",
            "action": "UPDATE",
            "description": "Update users",
        },
        {
            "name": "user_delete",
            "module": "users",
            "action": "DELETE",
            "description": "Delete users",
        },
        {
            "name": "user_manage_roles",
            "module": "users",
            "action": "UPDATE",
            "description": "Manage user roles",
        },
        # System Administration Permissions
        {
            "name": "system_admin",
            "module": "system",
            "action": "UPDATE",
            "description": "System administration",
        },
        {
            "name": "system_backup",
            "module": "system",
            "action": "CREATE",
            "description": "Create system backups",
        },
        {
            "name": "system_restore",
            "module": "system",
            "action": "UPDATE",
            "description": "Restore system backups",
        },
        {
            "name": "system_logs",
            "module": "system",
            "action": "READ",
            "description": "View system logs",
        },
        # AgScore and Assessment Permissions
        {
            "name": "agscore_read",
            "module": "agscore",
            "action": "READ",
            "description": "View AgScore assessments",
        },
        {
            "name": "agscore_update",
            "module": "agscore",
            "action": "UPDATE",
            "description": "Update AgScore assessments",
        },
        {
            "name": "agscore_calculate",
            "module": "agscore",
            "action": "CREATE",
            "description": "Calculate AgScore",
        },
        # Field Operations Permissions
        {
            "name": "field_visit_create",
            "module": "field",
            "action": "CREATE",
            "description": "Log field visits",
        },
        {
            "name": "field_visit_read",
            "module": "field",
            "action": "READ",
            "description": "View field visits",
        },
        {
            "name": "field_visit_update",
            "module": "field",
            "action": "UPDATE",
            "description": "Update field visits",
        },
        {
            "name": "field_data_update",
            "module": "field",
            "action": "UPDATE",
            "description": "Update field data",
        },
    ]

    created_permissions = []
    for perm_data in permissions:
        # Check if permission already exists
        existing_perm = Permission.query.filter_by(name=perm_data["name"]).first()
        if not existing_perm:
            permission = Permission(
                name=perm_data["name"],
                module=perm_data["module"],
                action=perm_data["action"],
                description=perm_data["description"],
            )
            db.session.add(permission)
            created_permissions.append(permission)
        else:
            created_permissions.append(existing_perm)

    db.session.commit()
    print(f"✅ Created/verified {len(created_permissions)} permissions")
    return created_permissions


def create_roles_and_assign_permissions():
    """Create roles and assign appropriate permissions"""

    # Get all permissions
    all_permissions = Permission.query.all()
    perm_dict = {p.name: p for p in all_permissions}

    # Define roles and their permissions
    roles_config = {
        "Super Admin": {
            "description": "Full system access with all administrative privileges",
            "permissions": [p.name for p in all_permissions],  # All permissions
        },
        "CARD MRI Manager": {
            "description": "Branch/Regional manager with oversight and approval capabilities",
            "permissions": [
                # Farmer management - full access to assigned region
                "farmer_create",
                "farmer_read",
                "farmer_update",
                "farmer_read_all",
                # Product management - read access
                "product_read",
                # Order management - full access with approval
                "order_create",
                "order_read",
                "order_update",
                "order_approve",
                "order_read_all",
                # Partner management - read and update
                "partner_read",
                "partner_update",
                # Financial - read access to regional data
                "financial_read",
                "financial_read_assigned",
                # Loan management - full approval authority
                "loan_read",
                "loan_update",
                "loan_approve",
                "loan_reject",
                "loan_disburse",
                # Reporting - comprehensive access
                "report_read",
                "report_create",
                "report_export",
                "report_read_all",
                # User management - limited to team members
                "user_read",
                "user_update",
                # AgScore - read and update
                "agscore_read",
                "agscore_update",
                "agscore_calculate",
                # Field operations - oversight
                "field_visit_read",
                "field_visit_update",
                "field_data_update",
            ],
        },
        "CARD MRI Officer": {
            "description": "Loan officer with farmer management and loan processing capabilities",
            "permissions": [
                # Farmer management - full CRUD for assigned farmers
                "farmer_create",
                "farmer_read",
                "farmer_update",
                "farmer_read_assigned",
                # Product management - read access
                "product_read",
                # Order management - create and read assigned
                "order_create",
                "order_read",
                "order_update",
                "order_read_assigned",
                # Partner management - read access
                "partner_read",
                # Financial - read assigned data
                "financial_read_assigned",
                # Loan management - create and process (not approve)
                "loan_create",
                "loan_read",
                "loan_update",
                # Reporting - assigned data
                "report_read",
                "report_read_assigned",
                "report_export",
                # AgScore - full assessment capabilities
                "agscore_read",
                "agscore_update",
                "agscore_calculate",
                # Field operations - full access
                "field_visit_create",
                "field_visit_read",
                "field_visit_update",
                "field_data_update",
            ],
        },
    }

    created_roles = []
    for role_name, role_config in roles_config.items():
        # Check if role already exists
        existing_role = Role.query.filter_by(name=role_name).first()
        if existing_role:
            role = existing_role
            # Clear existing permissions
            RolePermission.query.filter_by(role_id=role.id).delete()
        else:
            role = Role(name=role_name, description=role_config["description"])
            db.session.add(role)
            db.session.flush()  # Get the role ID

        # Assign permissions
        for perm_name in role_config["permissions"]:
            if perm_name in perm_dict:
                role_perm = RolePermission(
                    role_id=role.id, permission_id=perm_dict[perm_name].id
                )
                db.session.add(role_perm)

        created_roles.append(role)

    db.session.commit()
    print(f"✅ Created/updated {len(created_roles)} roles with permissions")
    return created_roles


def create_demo_users():
    """Create demo users for each role"""

    # Get roles
    super_admin_role = Role.query.filter_by(name="Super Admin").first()
    manager_role = Role.query.filter_by(name="CARD MRI Manager").first()
    officer_role = Role.query.filter_by(name="CARD MRI Officer").first()

    demo_users = [
        {
            "username": "admin",
            "email": "admin@magsasa-card.org",
            "password": "admin123",
            "first_name": "System",
            "last_name": "Administrator",
            "role": super_admin_role,
        },
        {
            "username": "manager1",
            "email": "manager1@magsasa-card.org",
            "password": "manager123",
            "first_name": "Maria",
            "last_name": "Santos",
            "role": manager_role,
        },
        {
            "username": "manager2",
            "email": "manager2@magsasa-card.org",
            "password": "manager123",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "role": manager_role,
        },
        {
            "username": "officer1",
            "email": "officer1@magsasa-card.org",
            "password": "officer123",
            "first_name": "Ana",
            "last_name": "Reyes",
            "role": officer_role,
        },
        {
            "username": "officer2",
            "email": "officer2@magsasa-card.org",
            "password": "officer123",
            "first_name": "Carlos",
            "last_name": "Garcia",
            "role": officer_role,
        },
        {
            "username": "officer3",
            "email": "officer3@magsasa-card.org",
            "password": "officer123",
            "first_name": "Rosa",
            "last_name": "Mendoza",
            "role": officer_role,
        },
    ]

    created_users = []
    for user_data in demo_users:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data["username"]).first()
        if not existing_user:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role_id=user_data["role"].id,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            user.set_password(user_data["password"])
            db.session.add(user)
            created_users.append(user)
        else:
            # Update existing user's role if needed
            existing_user.role_id = user_data["role"].id
            created_users.append(existing_user)

    db.session.commit()
    print(f"✅ Created/updated {len(created_users)} demo users")
    return created_users


def main():
    """Main implementation function"""
    print("🚀 Starting Phase 1 User Roles Implementation...")
    print("=" * 60)

    try:
        # Initialize Flask app and database
        app = init_app()

        with app.app_context():
            # Create permissions
            print("\n📋 Step 1: Creating Permissions...")
            permissions = create_permissions()

            # Create roles and assign permissions
            print("\n👥 Step 2: Creating Roles and Assigning Permissions...")
            roles = create_roles_and_assign_permissions()

            # Create demo users
            print("\n👤 Step 3: Creating Demo Users...")
            users = create_demo_users()

            print("\n" + "=" * 60)
            print("✅ Phase 1 Implementation Complete!")
            print("\n📊 Summary:")
            print(f"   • Permissions: {len(permissions)} created/verified")
            print(f"   • Roles: {len(roles)} created/updated")
            print(f"   • Users: {len(users)} created/updated")

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

            print("\n🎯 Next Steps:")
            print("   1. Test login with different user roles")
            print("   2. Verify role-based access controls")
            print("   3. Create role-specific dashboards")
            print("   4. Implement permission-based navigation")

    except Exception as e:
        print(f"❌ Error during implementation: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Phase 1 User Roles Implementation Successful!")
    else:
        print("\n💥 Phase 1 Implementation Failed!")
        sys.exit(1)

#!/usr/bin/env python3
"""
Fix farmer password hashes in the database
"""

import sqlite3

from werkzeug.security import generate_password_hash


def fix_farmer_passwords():
    """Fix farmer password hashes"""

    db_path = "/home/ubuntu/agsense_erp/src/agsense.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 Fixing farmer password hashes...")

        # Get all farmer users
        cursor.execute(
            """
            SELECT u.id, u.username, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'Farmer'
        """
        )
        farmer_users = cursor.fetchall()

        print(f"Found {len(farmer_users)} farmer users")

        # Update password hashes for all farmer users
        correct_password_hash = generate_password_hash("farmer123")

        for user_id, username, _role_name in farmer_users:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            """,
                (correct_password_hash, user_id),
            )

            print(f"✅ Updated password for {username}")

        # Commit changes
        conn.commit()
        print(f"🎉 Successfully updated passwords for {len(farmer_users)} farmer users")

        # Verify the fix
        print("\n🔍 Verifying password fixes...")
        from werkzeug.security import check_password_hash

        cursor.execute(
            """
            SELECT u.username, u.password_hash
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'Farmer'
        """
        )

        for username, password_hash in cursor.fetchall():
            is_valid = check_password_hash(password_hash, "farmer123")
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"  {username}: {status}")

    except Exception as e:
        print(f"❌ Error fixing farmer passwords: {e}")
        return False

    finally:
        if conn:
            conn.close()

    return True


if __name__ == "__main__":
    fix_farmer_passwords()

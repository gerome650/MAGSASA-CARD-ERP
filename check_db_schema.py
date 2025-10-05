#!/usr/bin/env python3
"""
Check database schema to understand table structures
"""

import os
import sqlite3


def check_database_schema():
    """Check the database schema for all tables"""

    db_path = "/home/ubuntu/agsense_erp/src/agsense.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print("📊 Database Schema Analysis")
        print("=" * 50)

        for (table_name,) in tables:
            print(f"\n🔍 Table: {table_name}")
            print("-" * 30)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            for column in columns:
                cid, name, type_, notnull, default, pk = column
                pk_indicator = " (PRIMARY KEY)" if pk else ""
                null_indicator = " NOT NULL" if notnull else ""
                default_indicator = f" DEFAULT {default}" if default else ""
                print(
                    f"  • {name}: {type_}{pk_indicator}{null_indicator}{default_indicator}"
                )

        # Check specific tables we need
        print("\n🎯 Key Tables for Phase 2:")
        print("=" * 50)

        key_tables = ["users", "roles", "permissions", "role_permissions", "farmers"]
        for table in key_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} records")

    except Exception as e:
        print(f"❌ Error checking database schema: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_database_schema()

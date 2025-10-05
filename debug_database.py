#!/usr/bin/env python3
"""
Debug database issues - check farmers table and data
"""

import os
import sqlite3


def debug_database():
    db_path = "src/agsense.db"

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    print(f"✅ Database file exists: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if farmers table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='farmers';"
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            print("❌ Farmers table does not exist")
            # Show all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("Available tables:", [table[0] for table in tables])
            return

        print("✅ Farmers table exists")

        # Check table schema
        cursor.execute("PRAGMA table_info(farmers);")
        columns = cursor.fetchall()
        print("\n📋 Farmers table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        # Count total farmers
        cursor.execute("SELECT COUNT(*) FROM farmers;")
        total_farmers = cursor.fetchone()[0]
        print(f"\n📊 Total farmers in database: {total_farmers}")

        if total_farmers > 0:
            # Show sample data
            cursor.execute(
                "SELECT id, full_name, address, crop_types, loan_status, agscore FROM farmers LIMIT 5;"
            )
            sample_farmers = cursor.fetchall()
            print("\n👥 Sample farmers:")
            for farmer in sample_farmers:
                print(
                    f"  ID: {farmer[0]}, Name: {farmer[1]}, Location: {farmer[2][:50]}..."
                )
                print(
                    f"      Crops: {farmer[3]}, Loan: {farmer[4]}, AgScore: {farmer[5]}"
                )

        conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")


if __name__ == "__main__":
    debug_database()

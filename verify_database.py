#!/usr/bin/env python3
"""
Verify that the database contains the fictitious farmers
"""

import sqlite3

# Database connection
conn = sqlite3.connect("src/agsense.db")
cursor = conn.cursor()


def verify_data():
    """Verify the database contains the expected data"""

    # Check total farmers
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total_farmers = cursor.fetchone()[0]
    print(f"Total farmers in database: {total_farmers}")

    # Check fictitious farmers
    cursor.execute("SELECT COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%'")
    fictitious_farmers = cursor.fetchone()[0]
    print(f"Fictitious farmers: {fictitious_farmers}")

    # Check some sample data
    cursor.execute(
        "SELECT first_name, last_name, email, crop_type, loan_amount FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%' LIMIT 5"
    )
    sample_farmers = cursor.fetchall()

    print("\nSample fictitious farmers:")
    for farmer in sample_farmers:
        print(f"  {farmer[0]} {farmer[1]} - {farmer[2]} - {farmer[3]} - ₱{farmer[4]}")

    # Check crop distribution
    cursor.execute(
        "SELECT crop_type, COUNT(*) FROM farmers WHERE notes LIKE '%FICTITIOUS DATA%' GROUP BY crop_type ORDER BY COUNT(*) DESC"
    )
    crop_dist = cursor.fetchall()

    print("\nCrop distribution:")
    for crop, count in crop_dist:
        print(f"  {crop}: {count} farmers")

    conn.close()

    return total_farmers, fictitious_farmers


if __name__ == "__main__":
    verify_data()

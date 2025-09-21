#!/usr/bin/env python3
"""
Verify and fix farmer data in the database
"""

import sqlite3
import os

def verify_and_fix_data():
    db_path = 'src/agsense.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current data
    cursor.execute("SELECT COUNT(*) FROM farmers WHERE email LIKE '%@agsense.ph'")
    enhanced_farmers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM farmers WHERE email LIKE '%@fictitious.com'")
    demo_farmers = cursor.fetchone()[0]
    
    print(f"📊 Current database status:")
    print(f"   Enhanced Filipino farmers: {enhanced_farmers}")
    print(f"   Demo farmers: {demo_farmers}")
    
    if enhanced_farmers == 0 and demo_farmers > 0:
        print("🔧 Found demo data instead of enhanced data. Need to regenerate...")
        
        # Clear old demo data
        cursor.execute("DELETE FROM farmers WHERE email LIKE '%@fictitious.com'")
        print("🗑️ Cleared old demo data")
        
        conn.commit()
        conn.close()
        
        # Regenerate enhanced data
        print("🌾 Regenerating enhanced Filipino farmers...")
        os.system("python3 generate_realistic_farmers.py")
        
    elif enhanced_farmers > 0:
        print("✅ Enhanced Filipino farmers found in database")
        
        # Show sample
        cursor.execute("SELECT full_name, address, crop_types, agscore FROM farmers LIMIT 3")
        samples = cursor.fetchall()
        print("\n👥 Sample farmers:")
        for farmer in samples:
            print(f"   {farmer[0]} - {farmer[1][:50]}... - {farmer[2]} - AgScore: {farmer[3]}")
    
    conn.close()

if __name__ == "__main__":
    verify_and_fix_data()


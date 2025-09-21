#!/usr/bin/env python3
"""
Generate Realistic Filipino Farmers using Enhanced Philippine Agricultural Data
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta

# Filipino first names (common names)
FILIPINO_FIRST_NAMES = [
    "Jose", "Maria", "Juan", "Ana", "Antonio", "Carmen", "Francisco", "Luz", "Manuel", "Rosa",
    "Pedro", "Elena", "Carlos", "Josefa", "Luis", "Esperanza", "Miguel", "Remedios", "Angel", "Concepcion",
    "Roberto", "Pilar", "Ricardo", "Dolores", "Eduardo", "Mercedes", "Fernando", "Gloria", "Alejandro", "Cristina",
    "Ramon", "Teresita", "Alfredo", "Rosario", "Ernesto", "Soledad", "Arturo", "Corazon", "Rodolfo", "Milagros",
    "Raul", "Natividad", "Armando", "Leonor", "Rogelio", "Pacita", "Danilo", "Lourdes", "Reynaldo", "Norma"
]

FILIPINO_LAST_NAMES = [
    "Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Tomas", "Andres",
    "Marquez", "Castillo", "Iglesias", "Villanueva", "Ramos", "Romero", "Lazaro", "Gonzales", "Aquino", "Flores",
    "Valdez", "Roque", "Gutierrez", "Tolentino", "Santiago", "Soriano", "Pascual", "Hernandez", "Dela Cruz", "Morales",
    "Aguilar", "Fernandez", "De Leon", "Manalo", "Perez", "Alvarez", "Rosales", "Mercado", "Rivera", "Castro",
    "Del Rosario", "Diaz", "Concepcion", "Rodriguez", "Lopez", "Evangelista mendoza", "Salazar", "Caballero", "Francisco", "Navarro"
]

# Mobile number prefixes in Philippines
MOBILE_PREFIXES = [
    "0917", "0918", "0919", "0920", "0921", "0928", "0929", "0939", "0949", "0950",
    "0908", "0909", "0910", "0912", "0930", "0938", "0946", "0947", "0948", "0951",
    "0813", "0817", "0905", "0906", "0915", "0916", "0926", "0927", "0935", "0936"
]

def get_database_data():
    """Retrieve enhanced data from database"""
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    # Get locations
    cursor.execute('SELECT full_location FROM locations')
    locations = [row[0] for row in cursor.fetchall()]
    
    # Get crops
    cursor.execute('SELECT name, typical_loan_min, typical_loan_max FROM crops')
    crops_data = cursor.fetchall()
    crops = {}
    for name, loan_min, loan_max in crops_data:
        crops[name] = {"loan_min": loan_min, "loan_max": loan_max}
    
    conn.close()
    
    return locations, crops

def calculate_agscore(farmer_data):
    """Calculate AgScore based on farmer characteristics"""
    score = 0
    
    # Farm Size (15% weight)
    farm_size = farmer_data.get('land_size_ha', 1.0)
    if farm_size <= 1.0:
        score += 60 * 0.15
    elif farm_size <= 2.0:
        score += 75 * 0.15
    elif farm_size <= 3.0:
        score += 85 * 0.15
    else:
        score += 95 * 0.15
    
    # Farming Experience (20% weight)
    experience = farmer_data.get('farming_experience', 5)
    if experience <= 2:
        score += 50 * 0.20
    elif experience <= 5:
        score += 70 * 0.20
    elif experience <= 10:
        score += 85 * 0.20
    else:
        score += 95 * 0.20
    
    # Land Tenure (20% weight)
    tenure = farmer_data.get('land_tenure', 'Owner-cultivator')
    tenure_scores = {
        'Tenant': 60,
        'Leaseholder': 75,
        'Owner-cultivator': 90,
        'Titled owner': 100
    }
    score += tenure_scores.get(tenure, 70) * 0.20
    
    # Crop Diversification (15% weight)
    crops = farmer_data.get('crop_types', 'Rice').split(', ')
    crop_count = len(crops)
    if crop_count == 1:
        score += 60 * 0.15
    elif crop_count == 2:
        score += 75 * 0.15
    elif crop_count == 3:
        score += 85 * 0.15
    else:
        score += 95 * 0.15
    
    # Previous Loan History (15% weight)
    score += random.choice([70, 90, 100, 40]) * 0.15
    
    # Technical Knowledge (15% weight)
    score += random.choice([60, 75, 90, 100]) * 0.15
    
    return min(max(int(score), 300), 1000)  # Ensure score is between 300-1000

def generate_loan_status_and_amount(crop_name, crops_data, agscore):
    """Generate realistic loan status and amount based on crop and AgScore"""
    if crop_name not in crops_data:
        loan_min, loan_max = 30000, 100000
    else:
        loan_min = crops_data[crop_name]["loan_min"]
        loan_max = crops_data[crop_name]["loan_max"]
    
    # Adjust loan amount based on AgScore
    if agscore >= 800:
        min_amount = max(loan_min, int(loan_max * 0.7))
        max_amount = loan_max
        loan_status = random.choices(
            ['Approved', 'Disbursed', 'Repaying', 'Pending'],
            weights=[30, 25, 20, 25]
        )[0]
    elif agscore >= 650:
        min_amount = max(loan_min, int(loan_max * 0.4))
        max_amount = int(loan_max * 0.8)
        loan_status = random.choices(
            ['Approved', 'Disbursed', 'Pending', 'Under Review'],
            weights=[25, 20, 35, 20]
        )[0]
    elif agscore >= 500:
        min_amount = loan_min
        max_amount = max(loan_min + 10000, int(loan_max * 0.5))
        loan_status = random.choices(
            ['Pending', 'Under Review', 'Approved', 'Rejected'],
            weights=[40, 25, 20, 15]
        )[0]
    else:
        min_amount = loan_min
        max_amount = max(loan_min + 5000, int(loan_max * 0.3))
        loan_status = random.choices(
            ['Pending', 'Rejected', 'Under Review'],
            weights=[30, 50, 20]
        )[0]
    
    # Ensure min_amount is never greater than max_amount
    if min_amount > max_amount:
        min_amount = loan_min
        max_amount = max(loan_min + 10000, loan_max)
    
    loan_amount = random.randint(min_amount, max_amount)
    
    return loan_amount, loan_status

def generate_realistic_farmer(locations, crops_data):
    """Generate a single realistic Filipino farmer"""
    
    # Basic information
    first_name = random.choice(FILIPINO_FIRST_NAMES)
    last_name = random.choice(FILIPINO_LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    
    # Location
    location = random.choice(locations)
    
    # Farm details
    land_size = round(random.uniform(0.5, 5.0), 1)
    farming_experience = random.randint(1, 25)
    land_tenure = random.choices(
        ['Titled owner', 'Owner-cultivator', 'Leaseholder', 'Tenant'],
        weights=[20, 40, 25, 15]
    )[0]
    
    # Crop selection (1-3 crops per farmer)
    available_crops = list(crops_data.keys())
    num_crops = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
    selected_crops = random.sample(available_crops, num_crops)
    crop_types = ', '.join(selected_crops)
    primary_crop = selected_crops[0]
    
    # Contact information
    mobile_prefix = random.choice(MOBILE_PREFIXES)
    mobile_suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    mobile_number = f"{mobile_prefix}{mobile_suffix}"
    
    email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}.fictitious@agsense.ph"
    
    # Government ID
    government_id = f"SSS-{random.randint(10, 99)}-{random.randint(1000000, 9999999)}-{random.randint(0, 9)}"
    
    # Create farmer data for AgScore calculation
    farmer_data = {
        'land_size_ha': land_size,
        'farming_experience': farming_experience,
        'land_tenure': land_tenure,
        'crop_types': crop_types
    }
    
    # Calculate AgScore
    agscore = calculate_agscore(farmer_data)
    
    # Determine AgScore grade
    if agscore >= 800:
        agscore_grade = 'Excellent'
    elif agscore >= 700:
        agscore_grade = 'Good'
    elif agscore >= 600:
        agscore_grade = 'Fair'
    else:
        agscore_grade = 'Poor'
    
    # Generate loan information
    loan_amount, loan_status = generate_loan_status_and_amount(primary_crop, crops_data, agscore)
    
    # Registration date (within last 2 years)
    start_date = datetime.now() - timedelta(days=730)  # 2 years ago
    end_date = datetime.now()
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    registration_date = start_date + timedelta(days=random_days)
    
    # Risk factors based on AgScore
    risk_factors = []
    if agscore < 600:
        risk_factors.extend(['Low AgScore', 'Limited farming experience'])
    if land_size < 1.0:
        risk_factors.append('Small farm size')
    if land_tenure in ['Tenant', 'Leaseholder']:
        risk_factors.append('Land tenure risk')
    
    risk_factors_str = ', '.join(risk_factors) if risk_factors else 'Low risk'
    
    return {
        'full_name': full_name,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'mobile_number': mobile_number,
        'government_id': government_id,
        'address': location,
        'land_size_ha': land_size,
        'crop_types': crop_types,
        'land_tenure': land_tenure,
        'farming_experience': farming_experience,
        'agscore': agscore,
        'agscore_grade': agscore_grade,
        'loan_amount': loan_amount,
        'loan_status': loan_status,
        'risk_factors': risk_factors_str,
        'registration_date': registration_date,
        'notes': 'FICTITIOUS DATA - Generated for testing and demonstration purposes'
    }

def create_farmers_table():
    """Create or update farmers table with enhanced schema"""
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    # Drop existing farmers table to recreate with new schema
    cursor.execute('DROP TABLE IF EXISTS farmers')
    
    # Create farmers table with comprehensive schema
    cursor.execute('''
        CREATE TABLE farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            mobile_number TEXT,
            government_id TEXT,
            address TEXT,
            land_size_ha REAL,
            crop_types TEXT,
            land_tenure TEXT,
            farming_experience INTEGER,
            agscore INTEGER,
            agscore_grade TEXT,
            loan_amount REAL,
            loan_status TEXT,
            risk_factors TEXT,
            registration_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_farmers(num_farmers=2500):
    """Generate specified number of realistic farmers"""
    print(f"Generating {num_farmers} realistic Filipino farmers...")
    
    # Get enhanced data
    locations, crops_data = get_database_data()
    
    if not locations or not crops_data:
        print("Error: Enhanced data not found. Please run enhance_philippine_data.py first.")
        return
    
    # Create farmers table
    create_farmers_table()
    
    # Connect to database
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    farmers_created = 0
    batch_size = 100
    
    for i in range(0, num_farmers, batch_size):
        batch_farmers = []
        batch_end = min(i + batch_size, num_farmers)
        
        for j in range(i, batch_end):
            farmer = generate_realistic_farmer(locations, crops_data)
            batch_farmers.append(farmer)
        
        # Insert batch
        cursor.executemany('''
            INSERT INTO farmers (
                full_name, first_name, last_name, email, mobile_number, government_id,
                address, land_size_ha, crop_types, land_tenure, farming_experience,
                agscore, agscore_grade, loan_amount, loan_status, risk_factors,
                registration_date, notes
            ) VALUES (
                :full_name, :first_name, :last_name, :email, :mobile_number, :government_id,
                :address, :land_size_ha, :crop_types, :land_tenure, :farming_experience,
                :agscore, :agscore_grade, :loan_amount, :loan_status, :risk_factors,
                :registration_date, :notes
            )
        ''', batch_farmers)
        
        farmers_created += len(batch_farmers)
        print(f"Created {farmers_created}/{num_farmers} farmers...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully generated {farmers_created} realistic Filipino farmers!")
    return farmers_created

def generate_statistics_report():
    """Generate statistics report for the created farmers"""
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    # Total farmers
    cursor.execute('SELECT COUNT(*) FROM farmers')
    total_farmers = cursor.fetchone()[0]
    
    # Crop distribution
    cursor.execute('''
        SELECT crop_types, COUNT(*) as count 
        FROM farmers 
        GROUP BY crop_types 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    crop_distribution = cursor.fetchall()
    
    # Loan status distribution
    cursor.execute('''
        SELECT loan_status, COUNT(*) as count 
        FROM farmers 
        GROUP BY loan_status 
        ORDER BY count DESC
    ''')
    loan_status_dist = cursor.fetchall()
    
    # AgScore distribution
    cursor.execute('''
        SELECT agscore_grade, COUNT(*) as count, AVG(agscore) as avg_score
        FROM farmers 
        GROUP BY agscore_grade 
        ORDER BY avg_score DESC
    ''')
    agscore_dist = cursor.fetchall()
    
    # Location distribution (top 10)
    cursor.execute('''
        SELECT address, COUNT(*) as count 
        FROM farmers 
        GROUP BY address 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    location_dist = cursor.fetchall()
    
    conn.close()
    
    # Generate report
    report = f"""
# Enhanced Filipino Farmers Dataset Report

## Overview
- **Total Farmers:** {total_farmers:,}
- **Data Source:** Enhanced Philippine Agricultural Database
- **Generation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Crop Distribution (Top 10)
"""
    
    for crop, count in crop_distribution:
        percentage = (count / total_farmers) * 100
        report += f"- **{crop}:** {count:,} farmers ({percentage:.1f}%)\n"
    
    report += "\n## Loan Status Distribution\n"
    for status, count in loan_status_dist:
        percentage = (count / total_farmers) * 100
        report += f"- **{status}:** {count:,} farmers ({percentage:.1f}%)\n"
    
    report += "\n## AgScore Distribution\n"
    for grade, count, avg_score in agscore_dist:
        percentage = (count / total_farmers) * 100
        report += f"- **{grade}:** {count:,} farmers ({percentage:.1f}%) - Avg Score: {avg_score:.0f}\n"
    
    report += "\n## Geographic Distribution (Top 10)\n"
    for location, count in location_dist:
        percentage = (count / total_farmers) * 100
        report += f"- **{location}:** {count:,} farmers ({percentage:.1f}%)\n"
    
    report += """
## Data Quality Features
- ✅ Authentic Filipino names and locations
- ✅ Realistic crop combinations and farming practices
- ✅ AgScore-based loan amounts and approval rates
- ✅ Philippine mobile number formats
- ✅ Proper land tenure and farm size distributions
- ✅ CARD MRI loan process integration

## Usage Notes
- All farmers are clearly marked as fictitious data
- Email addresses use @agsense.ph domain for identification
- Data reflects realistic Philippine agricultural patterns
- Suitable for system testing, training, and demonstrations
"""
    
    # Save report
    with open('/home/ubuntu/enhanced_farmers_report.md', 'w') as f:
        f.write(report)
    
    print("📊 Statistics report saved to enhanced_farmers_report.md")

def main():
    """Main function"""
    print("🌾 Enhanced Filipino Farmers Generator")
    print("=====================================")
    
    # Generate farmers
    farmers_created = generate_farmers(2500)
    
    if farmers_created > 0:
        # Generate statistics report
        generate_statistics_report()
        
        print(f"\n🎉 Successfully created {farmers_created} realistic Filipino farmers!")
        print("📊 Enhanced with Philippine locations, crops, and loan processes")
        print("📋 Statistics report available in enhanced_farmers_report.md")

if __name__ == "__main__":
    main()


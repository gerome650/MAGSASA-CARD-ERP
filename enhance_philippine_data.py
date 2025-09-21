#!/usr/bin/env python3
"""
Enhanced Philippine Agricultural Data for AgSense ERP
This script populates the system with realistic Philippine locations, crops, and loan processes
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random

# Philippine Regions and Provinces with Agricultural Focus
PHILIPPINE_LOCATIONS = {
    "Luzon": {
        "Central Luzon": [
            "Nueva Ecija - Cabanatuan City",
            "Nueva Ecija - Gapan City", 
            "Nueva Ecija - San Jose City",
            "Bulacan - Malolos City",
            "Bulacan - San Rafael",
            "Pampanga - San Fernando City",
            "Pampanga - Angeles City",
            "Tarlac - Tarlac City",
            "Tarlac - Gerona",
            "Zambales - Iba"
        ],
        "Cagayan Valley": [
            "Isabela - Ilagan City",
            "Isabela - Santiago City",
            "Cagayan - Tuguegarao City",
            "Nueva Vizcaya - Bayombong",
            "Quirino - Cabarroguis"
        ],
        "Ilocos Region": [
            "Ilocos Norte - Laoag City",
            "Ilocos Sur - Vigan City",
            "La Union - San Fernando City",
            "Pangasinan - Lingayen",
            "Pangasinan - Dagupan City"
        ],
        "CALABARZON": [
            "Laguna - Santa Cruz",
            "Laguna - Los Baños",
            "Batangas - Lipa City",
            "Cavite - Trece Martires City",
            "Rizal - Antipolo City",
            "Quezon - Lucena City"
        ]
    },
    "Visayas": {
        "Central Visayas": [
            "Cebu - Cebu City",
            "Cebu - Mandaue City",
            "Bohol - Tagbilaran City",
            "Negros Oriental - Dumaguete City",
            "Siquijor - Siquijor"
        ],
        "Western Visayas": [
            "Iloilo - Iloilo City",
            "Negros Occidental - Bacolod City",
            "Capiz - Roxas City",
            "Aklan - Kalibo",
            "Antique - San Jose de Buenavista",
            "Guimaras - Jordan"
        ],
        "Eastern Visayas": [
            "Leyte - Tacloban City",
            "Samar - Catbalogan City",
            "Eastern Samar - Borongan City",
            "Northern Samar - Catarman",
            "Southern Leyte - Maasin City",
            "Biliran - Naval"
        ]
    },
    "Mindanao": {
        "Northern Mindanao": [
            "Bukidnon - Malaybalay City",
            "Misamis Oriental - Cagayan de Oro City",
            "Misamis Occidental - Oroquieta City",
            "Camiguin - Mambajao",
            "Lanao del Norte - Tubod"
        ],
        "Davao Region": [
            "Davao del Sur - Davao City",
            "Davao del Norte - Tagum City",
            "Davao Oriental - Mati City",
            "Davao Occidental - Malita",
            "Davao de Oro - Nabunturan"
        ],
        "SOCCSKSARGEN": [
            "South Cotabato - Koronadal City",
            "Sultan Kudarat - Isulan",
            "Sarangani - Alabel",
            "General Santos City"
        ]
    }
}

# Philippine Crops with Seasonal Information
PHILIPPINE_CROPS = {
    "Rice": {
        "varieties": ["IR64", "PSB Rc82", "NSIC Rc222", "NSIC Rc216", "PSB Rc18"],
        "seasons": ["Wet Season (June-November)", "Dry Season (December-May)"],
        "regions": ["Central Luzon", "Cagayan Valley", "Western Visayas", "Central Visayas"],
        "avg_yield_per_hectare": "4.5 tons",
        "typical_loan_amount": (50000, 150000),
        "growth_period_days": 120,
        "fertilizer_needs": ["Urea", "Complete Fertilizer (14-14-14)", "Muriate of Potash"]
    },
    "Corn": {
        "varieties": ["Pioneer 30G68", "Dekalb 818", "NK 6410", "Bioseed 9681"],
        "seasons": ["Year-round with proper irrigation"],
        "regions": ["Northern Mindanao", "Cagayan Valley", "Central Luzon"],
        "avg_yield_per_hectare": "8.2 tons",
        "typical_loan_amount": (40000, 120000),
        "growth_period_days": 90,
        "fertilizer_needs": ["Urea", "Complete Fertilizer (16-16-16)", "Zinc Sulfate"]
    },
    "Sugarcane": {
        "varieties": ["Phil 8013", "Phil 99-1943", "VMC 86-550"],
        "seasons": ["Plant: October-December, Harvest: February-May"],
        "regions": ["Western Visayas", "Central Luzon", "Northern Mindanao"],
        "avg_yield_per_hectare": "65 tons",
        "typical_loan_amount": (80000, 250000),
        "growth_period_days": 365,
        "fertilizer_needs": ["Urea", "Complete Fertilizer (14-14-14)", "Muriate of Potash", "Zinc Sulfate"]
    },
    "Coconut": {
        "varieties": ["Malayan Dwarf", "Laguna Tall", "Catigan Green Dwarf"],
        "seasons": ["Year-round production"],
        "regions": ["CALABARZON", "Eastern Visayas", "Davao Region"],
        "avg_yield_per_hectare": "1.2 tons copra",
        "typical_loan_amount": (30000, 100000),
        "growth_period_days": 2555,  # 7 years to maturity
        "fertilizer_needs": ["Complete Fertilizer (14-14-14)", "Muriate of Potash", "Salt"]
    },
    "Banana": {
        "varieties": ["Cavendish", "Lakatan", "Saba", "Señorita"],
        "seasons": ["Year-round with proper care"],
        "regions": ["Davao Region", "Northern Mindanao", "SOCCSKSARGEN"],
        "avg_yield_per_hectare": "25 tons",
        "typical_loan_amount": (60000, 180000),
        "growth_period_days": 270,
        "fertilizer_needs": ["Urea", "Complete Fertilizer (14-14-14)", "Muriate of Potash"]
    },
    "Coffee": {
        "varieties": ["Robusta", "Arabica", "Liberica", "Excelsa"],
        "seasons": ["Harvest: October-February"],
        "regions": ["Northern Mindanao", "CALABARZON", "Central Visayas"],
        "avg_yield_per_hectare": "0.8 tons",
        "typical_loan_amount": (45000, 130000),
        "growth_period_days": 1095,  # 3 years to maturity
        "fertilizer_needs": ["Complete Fertilizer (14-14-14)", "Organic Fertilizer"]
    },
    "Cacao": {
        "varieties": ["UIT1", "BR25", "K9", "S106"],
        "seasons": ["Year-round harvest with peaks"],
        "regions": ["Davao Region", "Northern Mindanao", "Eastern Visayas"],
        "avg_yield_per_hectare": "0.5 tons",
        "typical_loan_amount": (55000, 160000),
        "growth_period_days": 1095,  # 3 years to maturity
        "fertilizer_needs": ["Complete Fertilizer (12-12-17)", "Organic Fertilizer"]
    },
    "Mango": {
        "varieties": ["Carabao", "Pico", "Indian", "Apple Mango"],
        "seasons": ["Harvest: March-June"],
        "regions": ["Central Luzon", "Ilocos Region", "Western Visayas"],
        "avg_yield_per_hectare": "8 tons",
        "typical_loan_amount": (70000, 200000),
        "growth_period_days": 1460,  # 4 years to maturity
        "fertilizer_needs": ["Complete Fertilizer (14-14-14)", "Muriate of Potash"]
    },
    "Vegetables": {
        "varieties": ["Tomato", "Eggplant", "Okra", "Ampalaya", "Sitaw", "Kangkong"],
        "seasons": ["Dry Season preferred for most"],
        "regions": ["CALABARZON", "Central Luzon", "Northern Mindanao"],
        "avg_yield_per_hectare": "15 tons",
        "typical_loan_amount": (25000, 80000),
        "growth_period_days": 75,
        "fertilizer_needs": ["Complete Fertilizer (14-14-14)", "Organic Fertilizer"]
    },
    "Rubber": {
        "varieties": ["RRIM 600", "PB 235", "GT 1"],
        "seasons": ["Year-round tapping after maturity"],
        "regions": ["CALABARZON", "Northern Mindanao", "Eastern Visayas"],
        "avg_yield_per_hectare": "1.5 tons latex",
        "typical_loan_amount": (90000, 280000),
        "growth_period_days": 2190,  # 6 years to maturity
        "fertilizer_needs": ["Complete Fertilizer (12-12-17)", "Muriate of Potash"]
    }
}

# CARD MRI Loan Process Stages
LOAN_PROCESS_STAGES = {
    "Application": {
        "description": "Farmer submits loan application with required documents",
        "required_documents": [
            "Barangay Certificate",
            "Valid ID (Driver's License, Voter's ID, etc.)",
            "Certificate of Land Ownership/Tenancy",
            "Farm Plan and Budget",
            "Proof of Income (if applicable)"
        ],
        "duration_days": 1,
        "responsible_party": "Farmer"
    },
    "Initial Review": {
        "description": "CARD MRI Field Officer reviews application completeness",
        "activities": [
            "Document verification",
            "Initial eligibility check",
            "Farm visit scheduling"
        ],
        "duration_days": 3,
        "responsible_party": "CARD MRI Field Officer"
    },
    "Farm Assessment": {
        "description": "On-site farm evaluation and farmer interview",
        "activities": [
            "Farm size verification",
            "Soil quality assessment",
            "Infrastructure evaluation",
            "Farmer capability assessment",
            "AgScore calculation"
        ],
        "duration_days": 2,
        "responsible_party": "CARD MRI Field Officer"
    },
    "Credit Analysis": {
        "description": "Detailed financial and risk assessment",
        "activities": [
            "Income analysis",
            "Debt-to-income ratio calculation",
            "Risk assessment",
            "Loan amount determination",
            "Repayment capacity evaluation"
        ],
        "duration_days": 5,
        "responsible_party": "CARD MRI Credit Analyst"
    },
    "Management Review": {
        "description": "Senior management approval process",
        "activities": [
            "Application review",
            "Risk evaluation",
            "Final approval decision"
        ],
        "duration_days": 3,
        "responsible_party": "CARD MRI Management"
    },
    "Loan Approval": {
        "description": "Loan approved and documentation prepared",
        "activities": [
            "Loan agreement preparation",
            "Terms and conditions finalization",
            "Disbursement scheduling"
        ],
        "duration_days": 2,
        "responsible_party": "CARD MRI Loan Officer"
    },
    "Disbursement": {
        "description": "Loan amount released to farmer",
        "activities": [
            "Final document signing",
            "Fund transfer",
            "Disbursement confirmation"
        ],
        "duration_days": 1,
        "responsible_party": "CARD MRI Cashier"
    },
    "Monitoring": {
        "description": "Ongoing loan and farm monitoring",
        "activities": [
            "Regular farm visits",
            "Progress monitoring",
            "Technical assistance",
            "Repayment tracking"
        ],
        "duration_days": 365,  # Ongoing throughout loan term
        "responsible_party": "CARD MRI Field Officer"
    }
}

# AgScore Calculation Factors
AGSCORE_FACTORS = {
    "Farm Size": {
        "weight": 0.15,
        "scoring": {
            "0.5-1.0 hectares": 60,
            "1.1-2.0 hectares": 75,
            "2.1-3.0 hectares": 85,
            "3.1+ hectares": 95
        }
    },
    "Farming Experience": {
        "weight": 0.20,
        "scoring": {
            "0-2 years": 50,
            "3-5 years": 70,
            "6-10 years": 85,
            "11+ years": 95
        }
    },
    "Crop Diversification": {
        "weight": 0.15,
        "scoring": {
            "Single crop": 60,
            "2 crops": 75,
            "3 crops": 85,
            "4+ crops": 95
        }
    },
    "Land Tenure": {
        "weight": 0.20,
        "scoring": {
            "Tenant": 60,
            "Leaseholder": 75,
            "Owner-cultivator": 90,
            "Titled owner": 100
        }
    },
    "Previous Loan History": {
        "weight": 0.15,
        "scoring": {
            "No history": 70,
            "Good repayment": 90,
            "Excellent repayment": 100,
            "Poor repayment": 40
        }
    },
    "Technical Knowledge": {
        "weight": 0.15,
        "scoring": {
            "Basic": 60,
            "Intermediate": 75,
            "Advanced": 90,
            "Expert": 100
        }
    }
}

def create_enhanced_database():
    """Create enhanced database with Philippine agricultural data"""
    conn = sqlite3.connect('src/agsense.db')
    cursor = conn.cursor()
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            sub_region TEXT NOT NULL,
            province_city TEXT NOT NULL,
            full_location TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create crops table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            varieties TEXT,
            seasons TEXT,
            suitable_regions TEXT,
            avg_yield_per_hectare TEXT,
            typical_loan_min INTEGER,
            typical_loan_max INTEGER,
            growth_period_days INTEGER,
            fertilizer_needs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create loan_process_stages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_process_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_name TEXT NOT NULL,
            description TEXT,
            activities TEXT,
            required_documents TEXT,
            duration_days INTEGER,
            responsible_party TEXT,
            stage_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create agscore_factors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agscore_factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factor_name TEXT NOT NULL,
            weight REAL,
            scoring_criteria TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def populate_locations(conn):
    """Populate locations table with Philippine data"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM locations')
    
    for region, sub_regions in PHILIPPINE_LOCATIONS.items():
        for sub_region, locations in sub_regions.items():
            for location in locations:
                full_location = f"{location}, {sub_region}, {region}"
                cursor.execute('''
                    INSERT INTO locations (region, sub_region, province_city, full_location)
                    VALUES (?, ?, ?, ?)
                ''', (region, sub_region, location, full_location))
    
    conn.commit()
    print(f"Populated {cursor.rowcount} locations")

def populate_crops(conn):
    """Populate crops table with Philippine crop data"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM crops')
    
    for crop_name, crop_data in PHILIPPINE_CROPS.items():
        cursor.execute('''
            INSERT INTO crops (
                name, varieties, seasons, suitable_regions, avg_yield_per_hectare,
                typical_loan_min, typical_loan_max, growth_period_days, fertilizer_needs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            crop_name,
            json.dumps(crop_data["varieties"]),
            json.dumps(crop_data["seasons"]),
            json.dumps(crop_data["regions"]),
            crop_data["avg_yield_per_hectare"],
            crop_data["typical_loan_amount"][0],
            crop_data["typical_loan_amount"][1],
            crop_data["growth_period_days"],
            json.dumps(crop_data["fertilizer_needs"])
        ))
    
    conn.commit()
    print(f"Populated {cursor.rowcount} crops")

def populate_loan_process(conn):
    """Populate loan process stages"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM loan_process_stages')
    
    for i, (stage_name, stage_data) in enumerate(LOAN_PROCESS_STAGES.items(), 1):
        activities = stage_data.get("activities", [])
        required_docs = stage_data.get("required_documents", [])
        
        cursor.execute('''
            INSERT INTO loan_process_stages (
                stage_name, description, activities, required_documents,
                duration_days, responsible_party, stage_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            stage_name,
            stage_data["description"],
            json.dumps(activities),
            json.dumps(required_docs),
            stage_data["duration_days"],
            stage_data["responsible_party"],
            i
        ))
    
    conn.commit()
    print(f"Populated {cursor.rowcount} loan process stages")

def populate_agscore_factors(conn):
    """Populate AgScore factors"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM agscore_factors')
    
    for factor_name, factor_data in AGSCORE_FACTORS.items():
        cursor.execute('''
            INSERT INTO agscore_factors (factor_name, weight, scoring_criteria)
            VALUES (?, ?, ?)
        ''', (
            factor_name,
            factor_data["weight"],
            json.dumps(factor_data["scoring"])
        ))
    
    conn.commit()
    print(f"Populated {cursor.rowcount} AgScore factors")

def main():
    """Main function to enhance the database with Philippine agricultural data"""
    print("Enhancing AgSense ERP with detailed Philippine agricultural data...")
    
    # Create enhanced database
    conn = create_enhanced_database()
    
    # Populate all tables
    populate_locations(conn)
    populate_crops(conn)
    populate_loan_process(conn)
    populate_agscore_factors(conn)
    
    conn.close()
    
    print("\n✅ Successfully enhanced database with:")
    print("   📍 Comprehensive Philippine locations")
    print("   🌾 Detailed crop information")
    print("   💰 CARD MRI loan process stages")
    print("   📊 AgScore calculation factors")
    print("\nThe AgSense ERP system now has realistic Philippine agricultural data!")

if __name__ == "__main__":
    main()


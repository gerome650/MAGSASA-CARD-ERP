#!/usr/bin/env python3
"""
Populate Sample Farmers Data
Creates comprehensive sample farmer data for testing the AgSense ERP system
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import json
from datetime import datetime

from main import app, db
from models.farmer import Farmer
from services.ka_ani_gpt import ka_ani_service


def create_sample_farmers():
    """Create comprehensive sample farmer data"""

    # Sample farmer data with realistic Philippine agricultural information
    sample_farmers = [
        {
            "full_name": "Juan Carlos Dela Cruz",
            "mobile_number": "+639171234567",
            "email": "juan.delacruz@gmail.com",
            "date_of_birth": "1975-03-15",
            "address": "123 Rizal Street, Barangay San Jose",
            "barangay": "San Jose",
            "farm_location_gps": "14.2456, 121.0123",
            "farm_location_text": "Lot 5, Block 3, San Jose Agricultural Area, Calauan, Laguna",
            "land_size_ha": 2.5,
            "farming_experience": 15,
            "crop_types": "Rice, Corn",
            "land_tenure": "Owned",
            "digital_wallet": "09171234567",
            "bank_account": "BPI-1234567890",
            "loan_status": "Disbursed",
            "loan_amount": 75000,
        },
        {
            "full_name": "Maria Santos Reyes",
            "mobile_number": "+639281234568",
            "email": "maria.reyes@yahoo.com",
            "date_of_birth": "1980-07-22",
            "address": "456 Bonifacio Avenue, Barangay Santa Maria",
            "barangay": "Santa Maria",
            "farm_location_gps": "14.2789, 121.0456",
            "farm_location_text": "Sitio Malaking Bukid, Santa Maria, Bay, Laguna",
            "land_size_ha": 1.8,
            "farming_experience": 12,
            "crop_types": "Rice, Vegetables",
            "land_tenure": "Leased",
            "digital_wallet": "09281234568",
            "bank_account": "BDO-2345678901",
            "loan_status": "Repaying",
            "loan_amount": 45000,
        },
        {
            "full_name": "Roberto Villanueva Garcia",
            "mobile_number": "+639391234569",
            "email": "roberto.garcia@hotmail.com",
            "date_of_birth": "1970-11-08",
            "address": "789 Mabini Street, Barangay San Pedro",
            "barangay": "San Pedro",
            "farm_location_gps": "14.3012, 121.0789",
            "farm_location_text": "Hacienda San Pedro, Los Baños, Laguna",
            "land_size_ha": 4.2,
            "farming_experience": 25,
            "crop_types": "Rice, Sugarcane",
            "land_tenure": "Owned",
            "digital_wallet": "09391234569",
            "bank_account": "LBP-3456789012",
            "loan_status": "Approved",
            "loan_amount": 120000,
        },
        {
            "full_name": "Ana Luz Fernandez",
            "mobile_number": "+639451234570",
            "email": "ana.fernandez@gmail.com",
            "date_of_birth": "1985-01-30",
            "address": "321 Del Pilar Street, Barangay Santo Tomas",
            "barangay": "Santo Tomas",
            "farm_location_gps": "14.2234, 121.0234",
            "farm_location_text": "Cooperative Farm Area, Santo Tomas, Alaminos, Laguna",
            "land_size_ha": 1.2,
            "farming_experience": 8,
            "crop_types": "Vegetables, Herbs",
            "land_tenure": "Tenanted",
            "digital_wallet": "09451234570",
            "bank_account": "RCBC-4567890123",
            "loan_status": "Pending",
            "loan_amount": 25000,
        },
        {
            "full_name": "Pedro Miguel Aquino",
            "mobile_number": "+639561234571",
            "email": "pedro.aquino@outlook.com",
            "date_of_birth": "1978-09-12",
            "address": "654 Luna Street, Barangay San Antonio",
            "barangay": "San Antonio",
            "farm_location_gps": "14.2567, 121.0567",
            "farm_location_text": "Riverside Farm, San Antonio, Calauan, Laguna",
            "land_size_ha": 3.1,
            "farming_experience": 18,
            "crop_types": "Rice, Fish (Aquaculture)",
            "land_tenure": "Owned",
            "digital_wallet": "09561234571",
            "bank_account": "PNB-5678901234",
            "loan_status": "Repaid",
            "loan_amount": 85000,
        },
        {
            "full_name": "Carmen Rosa Mendoza",
            "mobile_number": "+639671234572",
            "email": "carmen.mendoza@gmail.com",
            "date_of_birth": "1982-05-18",
            "address": "987 Lapu-Lapu Street, Barangay San Miguel",
            "barangay": "San Miguel",
            "farm_location_gps": "14.2890, 121.0890",
            "farm_location_text": "Organic Farm Cooperative, San Miguel, Bay, Laguna",
            "land_size_ha": 2.0,
            "farming_experience": 10,
            "crop_types": "Organic Rice, Organic Vegetables",
            "land_tenure": "Leased",
            "digital_wallet": "09671234572",
            "bank_account": "UBP-6789012345",
            "loan_status": "None",
            "loan_amount": None,
        },
        {
            "full_name": "Jose Antonio Ramos",
            "mobile_number": "+639781234573",
            "email": "jose.ramos@yahoo.com",
            "date_of_birth": "1973-12-03",
            "address": "147 Magallanes Avenue, Barangay San Rafael",
            "barangay": "San Rafael",
            "farm_location_gps": "14.3123, 121.0123",
            "farm_location_text": "Highland Farm, San Rafael, Los Baños, Laguna",
            "land_size_ha": 5.5,
            "farming_experience": 22,
            "crop_types": "Rice, Corn, Coconut",
            "land_tenure": "Owned",
            "digital_wallet": "09781234573",
            "bank_account": "MB-7890123456",
            "loan_status": "Disbursed",
            "loan_amount": 150000,
        },
        {
            "full_name": "Luz Marina Torres",
            "mobile_number": "+639891234574",
            "email": "luz.torres@hotmail.com",
            "date_of_birth": "1987-04-25",
            "address": "258 Quezon Boulevard, Barangay Santa Cruz",
            "barangay": "Santa Cruz",
            "farm_location_gps": "14.2345, 121.0345",
            "farm_location_text": "Women's Cooperative Farm, Santa Cruz, Alaminos, Laguna",
            "land_size_ha": 1.5,
            "farming_experience": 6,
            "crop_types": "Vegetables, Flowers",
            "land_tenure": "Tenanted",
            "digital_wallet": "09891234574",
            "bank_account": "SB-8901234567",
            "loan_status": "Rejected",
            "loan_amount": None,
        },
        {
            "full_name": "Ricardo Flores Castillo",
            "mobile_number": "+639901234575",
            "email": "ricardo.castillo@gmail.com",
            "date_of_birth": "1976-08-14",
            "address": "369 Burgos Street, Barangay San Juan",
            "barangay": "San Juan",
            "farm_location_gps": "14.2678, 121.0678",
            "farm_location_text": "Integrated Farm, San Juan, Calauan, Laguna",
            "land_size_ha": 3.8,
            "farming_experience": 20,
            "crop_types": "Rice, Livestock, Poultry",
            "land_tenure": "Owned",
            "digital_wallet": "09901234575",
            "bank_account": "CB-9012345678",
            "loan_status": "Repaying",
            "loan_amount": 95000,
        },
        {
            "full_name": "Elena Grace Morales",
            "mobile_number": "+639011234576",
            "email": "elena.morales@outlook.com",
            "date_of_birth": "1984-06-09",
            "address": "741 Jacinto Street, Barangay San Lucas",
            "barangay": "San Lucas",
            "farm_location_gps": "14.2901, 121.0901",
            "farm_location_text": "Sustainable Agriculture Demo Farm, San Lucas, Bay, Laguna",
            "land_size_ha": 2.3,
            "farming_experience": 9,
            "crop_types": "Rice, Medicinal Plants",
            "land_tenure": "Leased",
            "digital_wallet": "09011234576",
            "bank_account": "EWB-0123456789",
            "loan_status": "Defaulted",
            "loan_amount": 35000,
        },
    ]

    print("Creating sample farmers...")

    with app.app_context():
        # Clear existing farmers (optional - comment out if you want to keep existing data)
        # Farmer.query.delete()
        # db.session.commit()

        created_farmers = []

        for farmer_data in sample_farmers:
            try:
                # Check if farmer already exists
                existing_farmer = Farmer.query.filter_by(
                    full_name=farmer_data["full_name"]
                ).first()

                if existing_farmer:
                    print(
                        f"Farmer {farmer_data['full_name']} already exists, skipping..."
                    )
                    continue

                # Create new farmer
                farmer = Farmer(
                    full_name=farmer_data["full_name"],
                    mobile_number=farmer_data["mobile_number"],
                    email=farmer_data["email"],
                    date_of_birth=datetime.strptime(
                        farmer_data["date_of_birth"], "%Y-%m-%d"
                    ).date(),
                    address=farmer_data["address"],
                    barangay=farmer_data["barangay"],
                    farm_location_gps=farmer_data["farm_location_gps"],
                    farm_location_text=farmer_data["farm_location_text"],
                    land_size_ha=farmer_data["land_size_ha"],
                    farming_experience=farmer_data["farming_experience"],
                    crop_types=farmer_data["crop_types"],
                    land_tenure=farmer_data["land_tenure"],
                    digital_wallet=farmer_data["digital_wallet"],
                    bank_account=farmer_data["bank_account"],
                    loan_status=farmer_data["loan_status"],
                    loan_amount=farmer_data["loan_amount"],
                )

                db.session.add(farmer)
                db.session.flush()  # Get the farmer ID

                # Generate AgScore using Ka-Ani GPT service
                print(f"Generating AgScore for {farmer.full_name}...")
                agscore_result = ka_ani_service.calculate_agscore(farmer.to_dict())

                if agscore_result["success"]:
                    farmer.update_agscore(
                        agscore_result["agscore"],
                        json.dumps(agscore_result["risk_factors"]),
                    )
                    print(f"  AgScore: {farmer.agscore} ({farmer.agscore_grade})")
                else:
                    print(f"  Failed to generate AgScore for {farmer.full_name}")

                created_farmers.append(farmer)

            except Exception as e:
                print(f"Error creating farmer {farmer_data['full_name']}: {str(e)}")
                db.session.rollback()
                continue

        # Commit all changes
        try:
            db.session.commit()
            print(f"\nSuccessfully created {len(created_farmers)} farmers!")

            # Print summary
            print("\n=== FARMER SUMMARY ===")
            for farmer in created_farmers:
                print(
                    f"ID: {farmer.id} | {farmer.full_name} | {farmer.barangay} | AgScore: {farmer.agscore or 'N/A'} | Loan: {farmer.loan_status}"
                )

        except Exception as e:
            print(f"Error committing farmers: {str(e)}")
            db.session.rollback()


def update_existing_farmers_with_agscore():
    """Update existing farmers with AgScore if they don't have one"""

    print("Updating existing farmers with AgScore...")

    with app.app_context():
        farmers_without_agscore = Farmer.query.filter(Farmer.agscore.is_(None)).all()

        print(f"Found {len(farmers_without_agscore)} farmers without AgScore")

        for farmer in farmers_without_agscore:
            try:
                print(f"Generating AgScore for {farmer.full_name or farmer.name}...")
                agscore_result = ka_ani_service.calculate_agscore(farmer.to_dict())

                if agscore_result["success"]:
                    farmer.update_agscore(
                        agscore_result["agscore"],
                        json.dumps(agscore_result["risk_factors"]),
                    )
                    print(f"  AgScore: {farmer.agscore} ({farmer.agscore_grade})")
                else:
                    print(
                        f"  Failed to generate AgScore for {farmer.full_name or farmer.name}"
                    )

            except Exception as e:
                print(
                    f"Error updating farmer {farmer.full_name or farmer.name}: {str(e)}"
                )
                continue

        try:
            db.session.commit()
            print(
                f"Successfully updated {len(farmers_without_agscore)} farmers with AgScore!"
            )
        except Exception as e:
            print(f"Error committing AgScore updates: {str(e)}")
            db.session.rollback()


def print_farmer_statistics():
    """Print statistics about farmers in the database"""

    with app.app_context():
        total_farmers = Farmer.query.count()
        farmers_with_agscore = Farmer.query.filter(Farmer.agscore.isnot(None)).count()

        print("\n=== FARMER STATISTICS ===")
        print(f"Total Farmers: {total_farmers}")
        print(f"Farmers with AgScore: {farmers_with_agscore}")
        print(f"Farmers without AgScore: {total_farmers - farmers_with_agscore}")

        # Loan status distribution
        loan_statuses = (
            db.session.query(Farmer.loan_status, db.func.count(Farmer.id))
            .group_by(Farmer.loan_status)
            .all()
        )
        print("\nLoan Status Distribution:")
        for status, count in loan_statuses:
            print(f"  {status or 'None'}: {count}")

        # AgScore grade distribution
        agscore_grades = (
            db.session.query(Farmer.agscore_grade, db.func.count(Farmer.id))
            .group_by(Farmer.agscore_grade)
            .all()
        )
        print("\nAgScore Grade Distribution:")
        for grade, count in agscore_grades:
            print(f"  {grade or 'None'}: {count}")


if __name__ == "__main__":
    print("AgSense ERP - Sample Farmer Data Population")
    print("=" * 50)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Create sample farmers
    create_sample_farmers()

    # Update existing farmers with AgScore
    update_existing_farmers_with_agscore()

    # Print statistics
    print_farmer_statistics()

    print("\n✅ Sample farmer data population completed!")

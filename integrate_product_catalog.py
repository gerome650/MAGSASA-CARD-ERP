#!/usr/bin/env python3
"""
AgSense ERP - Product Catalog Integration Script
Integrates the product catalog module into the existing ERP system
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.category import Category
from src.models.product import Product
from src.models.supplier import Supplier
from src.models.user import db


def create_sample_categories():
    """Create sample product categories"""
    categories_data = [
        # Main categories
        {
            "name": "Fertilizers",
            "description": "Chemical and organic fertilizers for crop nutrition",
        },
        {"name": "Seeds", "description": "High-quality seeds for various crops"},
        {
            "name": "Pesticides",
            "description": "Pest control products for crop protection",
        },
        {"name": "Herbicides", "description": "Weed control products"},
        {
            "name": "Tools & Equipment",
            "description": "Agricultural tools and farming equipment",
        },
        {"name": "Irrigation", "description": "Irrigation systems and components"},
    ]

    # Create main categories
    main_categories = {}
    for cat_data in categories_data:
        category = Category.query.filter_by(name=cat_data["name"]).first()
        if not category:
            category = Category(
                name=cat_data["name"], description=cat_data["description"]
            )
            db.session.add(category)
            db.session.flush()  # Get the ID
        main_categories[cat_data["name"]] = category.id

    # Create subcategories
    subcategories_data = [
        # Fertilizer subcategories
        {
            "name": "NPK Fertilizers",
            "parent": "Fertilizers",
            "description": "Nitrogen, Phosphorus, Potassium fertilizers",
        },
        {
            "name": "Urea",
            "parent": "Fertilizers",
            "description": "Nitrogen-rich urea fertilizers",
        },
        {
            "name": "Organic Fertilizers",
            "parent": "Fertilizers",
            "description": "Natural and organic fertilizers",
        },
        {
            "name": "Micronutrients",
            "parent": "Fertilizers",
            "description": "Essential micronutrient fertilizers",
        },
        # Seed subcategories
        {
            "name": "Rice Seeds",
            "parent": "Seeds",
            "description": "High-yield rice varieties",
        },
        {
            "name": "Corn Seeds",
            "parent": "Seeds",
            "description": "Hybrid corn varieties",
        },
        {
            "name": "Vegetable Seeds",
            "parent": "Seeds",
            "description": "Various vegetable seeds",
        },
        # Pesticide subcategories
        {
            "name": "Insecticides",
            "parent": "Pesticides",
            "description": "Insect control products",
        },
        {
            "name": "Fungicides",
            "parent": "Pesticides",
            "description": "Fungal disease control",
        },
        # Tool subcategories
        {
            "name": "Hand Tools",
            "parent": "Tools & Equipment",
            "description": "Manual farming tools",
        },
        {
            "name": "Power Tools",
            "parent": "Tools & Equipment",
            "description": "Motorized farming equipment",
        },
    ]

    for subcat_data in subcategories_data:
        subcategory = Category.query.filter_by(name=subcat_data["name"]).first()
        if not subcategory:
            subcategory = Category(
                name=subcat_data["name"],
                parent_id=main_categories[subcat_data["parent"]],
                description=subcat_data["description"],
            )
            db.session.add(subcategory)

    db.session.commit()
    print("✅ Sample categories created successfully")


def create_sample_suppliers():
    """Create sample suppliers"""
    suppliers_data = [
        {
            "name": "Atlas Fertilizer Corporation",
            "contact_person": "Maria Rodriguez",
            "email": "maria.rodriguez@atlas.com.ph",
            "phone": "+632-8123-4567",
            "address": "Makati City, Metro Manila, Philippines",
            "website": "https://atlas.com.ph",
            "payment_terms": "Net 30",
            "notes": "Leading fertilizer manufacturer in the Philippines",
        },
        {
            "name": "SL Agritech Corporation",
            "contact_person": "Henry Lim",
            "email": "henry.lim@slagritech.com",
            "phone": "+632-8234-5678",
            "address": "Quezon City, Metro Manila, Philippines",
            "website": "https://slagritech.com",
            "payment_terms": "Net 15",
            "notes": "Premium rice seed producer",
        },
        {
            "name": "Bayer CropScience Philippines",
            "contact_person": "Anna Santos",
            "email": "anna.santos@bayer.com",
            "phone": "+632-8345-6789",
            "address": "Taguig City, Metro Manila, Philippines",
            "website": "https://bayer.com.ph",
            "payment_terms": "Net 30",
            "notes": "Global crop protection solutions",
        },
        {
            "name": "East-West Seed Philippines",
            "contact_person": "Roberto Cruz",
            "email": "roberto.cruz@ewseed.com",
            "phone": "+632-8456-7890",
            "address": "Lipa City, Batangas, Philippines",
            "website": "https://ewseed.com",
            "payment_terms": "COD",
            "notes": "Vegetable seed specialist",
        },
        {
            "name": "Yanmar Philippines Inc.",
            "contact_person": "Takeshi Yamamoto",
            "email": "takeshi.yamamoto@yanmar.com.ph",
            "phone": "+632-8567-8901",
            "address": "Pasig City, Metro Manila, Philippines",
            "website": "https://yanmar.com.ph",
            "payment_terms": "Net 60",
            "notes": "Agricultural machinery and equipment",
        },
    ]

    for supplier_data in suppliers_data:
        supplier = Supplier.query.filter_by(name=supplier_data["name"]).first()
        if not supplier:
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)

    db.session.commit()
    print("✅ Sample suppliers created successfully")


def create_sample_products():
    """Create sample agricultural products"""

    # Get categories and suppliers
    fertilizer_cat = Category.query.filter_by(name="NPK Fertilizers").first()
    urea_cat = Category.query.filter_by(name="Urea").first()
    rice_seed_cat = Category.query.filter_by(name="Rice Seeds").first()
    insecticide_cat = Category.query.filter_by(name="Insecticides").first()

    atlas = Supplier.query.filter_by(name="Atlas Fertilizer Corporation").first()
    sl_agritech = Supplier.query.filter_by(name="SL Agritech Corporation").first()
    bayer = Supplier.query.filter_by(name="Bayer CropScience Philippines").first()

    products_data = [
        # Fertilizers
        {
            "sku": "ATL-NPK-14-14-14-50",
            "name": "Atlas Triple 14 (14-14-14)",
            "description": "Complete fertilizer with equal amounts of Nitrogen, Phosphorus, and Potassium",
            "brand": "Atlas",
            "category_id": fertilizer_cat.id if fertilizer_cat else 1,
            "uom": "bag",
            "unit_value": 50.0,
            "supplier_id": atlas.id if atlas else 1,
            "cost_price": 1200.00,
            "selling_price": 1450.00,
            "stock_on_hand": 150,
            "reorder_point": 20,
            "composition": "14% Nitrogen, 14% Phosphorus, 14% Potassium",
            "application_rate": "2-3 bags per hectare",
            "crop_suitability": "Rice, Corn, Vegetables",
            "season_suitability": "All seasons",
        },
        {
            "sku": "ATL-UREA-46-50",
            "name": "Atlas Urea 46-0-0",
            "description": "High nitrogen content fertilizer for vegetative growth",
            "brand": "Atlas",
            "category_id": urea_cat.id if urea_cat else 1,
            "uom": "bag",
            "unit_value": 50.0,
            "supplier_id": atlas.id if atlas else 1,
            "cost_price": 1100.00,
            "selling_price": 1320.00,
            "stock_on_hand": 200,
            "reorder_point": 30,
            "composition": "46% Nitrogen",
            "application_rate": "1-2 bags per hectare",
            "crop_suitability": "Rice, Corn, Sugarcane",
            "season_suitability": "All seasons",
        },
        {
            "sku": "ATL-NPK-16-20-0-50",
            "name": "Atlas Complete 16-20-0",
            "description": "Starter fertilizer with high phosphorus content",
            "brand": "Atlas",
            "category_id": fertilizer_cat.id if fertilizer_cat else 1,
            "uom": "bag",
            "unit_value": 50.0,
            "supplier_id": atlas.id if atlas else 1,
            "cost_price": 1250.00,
            "selling_price": 1500.00,
            "stock_on_hand": 80,
            "reorder_point": 15,
            "composition": "16% Nitrogen, 20% Phosphorus",
            "application_rate": "2 bags per hectare at planting",
            "crop_suitability": "Rice, Corn",
            "season_suitability": "Planting season",
        },
        # Seeds
        {
            "sku": "SLA-RICE-RC222-20",
            "name": "SL Agritech RC222 Hybrid Rice",
            "description": "High-yielding hybrid rice variety with disease resistance",
            "brand": "SL Agritech",
            "category_id": rice_seed_cat.id if rice_seed_cat else 2,
            "uom": "kg",
            "unit_value": 20.0,
            "supplier_id": sl_agritech.id if sl_agritech else 2,
            "cost_price": 180.00,
            "selling_price": 220.00,
            "stock_on_hand": 500,
            "reorder_point": 50,
            "composition": "Hybrid rice seeds",
            "application_rate": "20kg per hectare",
            "crop_suitability": "Irrigated lowland rice",
            "season_suitability": "Wet and dry season",
        },
        {
            "sku": "SLA-RICE-RC216-20",
            "name": "SL Agritech RC216 Premium Rice",
            "description": "Premium quality rice variety with excellent grain quality",
            "brand": "SL Agritech",
            "category_id": rice_seed_cat.id if rice_seed_cat else 2,
            "uom": "kg",
            "unit_value": 20.0,
            "supplier_id": sl_agritech.id if sl_agritech else 2,
            "cost_price": 200.00,
            "selling_price": 250.00,
            "stock_on_hand": 300,
            "reorder_point": 40,
            "composition": "Premium hybrid rice seeds",
            "application_rate": "18-20kg per hectare",
            "crop_suitability": "Irrigated lowland rice",
            "season_suitability": "Wet and dry season",
        },
        # Pesticides
        {
            "sku": "BAY-CONF-200SC-1L",
            "name": "Bayer Confidor 200SC",
            "description": "Systemic insecticide for sucking insects",
            "brand": "Bayer",
            "category_id": insecticide_cat.id if insecticide_cat else 3,
            "uom": "liter",
            "unit_value": 1.0,
            "supplier_id": bayer.id if bayer else 3,
            "cost_price": 2800.00,
            "selling_price": 3400.00,
            "stock_on_hand": 50,
            "reorder_point": 10,
            "composition": "200g/L Imidacloprid",
            "application_rate": "0.5-1L per hectare",
            "crop_suitability": "Rice, Vegetables, Fruits",
            "season_suitability": "All seasons",
        },
        {
            "sku": "BAY-BELT-480SC-1L",
            "name": "Bayer Belt 480SC",
            "description": "Broad spectrum insecticide for various pests",
            "brand": "Bayer",
            "category_id": insecticide_cat.id if insecticide_cat else 3,
            "uom": "liter",
            "unit_value": 1.0,
            "supplier_id": bayer.id if bayer else 3,
            "cost_price": 1800.00,
            "selling_price": 2200.00,
            "stock_on_hand": 75,
            "reorder_point": 15,
            "composition": "480g/L Chlorpyrifos",
            "application_rate": "1-2L per hectare",
            "crop_suitability": "Rice, Corn, Vegetables",
            "season_suitability": "All seasons",
        },
    ]

    for product_data in products_data:
        product = Product.query.filter_by(sku=product_data["sku"]).first()
        if not product:
            product = Product(**product_data)
            db.session.add(product)

    db.session.commit()
    print("✅ Sample products created successfully")


def main():
    """Main integration function"""
    print("🚀 Starting AgSense ERP Product Catalog Integration...")

    # Import Flask app and create application context
    from src.main import app

    with app.app_context():
        try:
            # Create database tables
            db.create_all()
            print("✅ Database tables created")

            # Create sample data
            create_sample_categories()
            create_sample_suppliers()
            create_sample_products()

            print("\n🎉 Product Catalog Integration Completed Successfully!")
            print("\n📊 Summary:")
            print(f"  • Categories: {Category.query.count()}")
            print(f"  • Suppliers: {Supplier.query.count()}")
            print(f"  • Products: {Product.query.count()}")

        except Exception as e:
            print(f"❌ Error during integration: {str(e)}")
            db.session.rollback()
            return False

    return True


if __name__ == "__main__":
    main()

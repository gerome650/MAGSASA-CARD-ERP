"""
KaAni Function Calling Module
Provides access to farmer data and ERP functionality for enhanced agricultural advice
"""

from datetime import datetime

from flask import session

from src.models.farmer import Farmer
from src.models.order import Order
from src.models.product import Product


class KaAniFunctions:
    """Function calling interface for KaAni to access ERP data"""

    @staticmethod
    def get_farmer_profile(farmer_id=None):
        """Get farmer profile information"""
        try:
            if not farmer_id:
                # Get current user's farmer profile
                user_id = session.get("user_id")
                if not user_id:
                    return {"error": "No user logged in"}

                farmer = Farmer.query.filter_by(user_id=user_id).first()
            else:
                farmer = Farmer.query.get(farmer_id)

            if not farmer:
                return {"error": "Farmer not found"}

            return {
                "farmer_id": farmer.id,
                "name": farmer.name,
                "location": farmer.location,
                "farm_size": farmer.farm_size,
                "primary_crops": farmer.primary_crops,
                "contact_number": farmer.contact_number,
                "email": farmer.email,
                "registration_date": (
                    farmer.created_at.isoformat() if farmer.created_at else None
                ),
                "status": "active",
            }

        except Exception as e:
            return {"error": f"Failed to get farmer profile: {str(e)}"}

    @staticmethod
    def get_farmer_orders(farmer_id=None, limit=10):
        """Get farmer's recent orders and input purchases"""
        try:
            if not farmer_id:
                user_id = session.get("user_id")
                if not user_id:
                    return {"error": "No user logged in"}

                farmer = Farmer.query.filter_by(user_id=user_id).first()
                if not farmer:
                    return {"error": "Farmer not found"}
                farmer_id = farmer.id

            orders = (
                Order.query.filter_by(farmer_id=farmer_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
                .all()
            )

            order_list = []
            for order in orders:
                order_items = []
                for item in order.items:
                    product = Product.query.get(item.product_id)
                    order_items.append(
                        {
                            "product_name": product.name if product else "Unknown",
                            "category": (
                                product.category.name
                                if product and product.category
                                else "Unknown"
                            ),
                            "quantity": item.quantity,
                            "unit_price": float(item.unit_price),
                            "total_price": float(item.total_price),
                        }
                    )

                order_list.append(
                    {
                        "order_id": order.id,
                        "order_date": order.created_at.isoformat(),
                        "status": order.status,
                        "total_amount": float(order.total_amount),
                        "items": order_items,
                    }
                )

            return {
                "farmer_id": farmer_id,
                "orders": order_list,
                "total_orders": len(order_list),
            }

        except Exception as e:
            return {"error": f"Failed to get farmer orders: {str(e)}"}

    @staticmethod
    def get_seasonal_recommendations(location=None, crop_type=None):
        """Get seasonal farming recommendations based on location and crop"""
        try:
            current_month = datetime.now().month

            # Philippine seasons
            if current_month in [12, 1, 2, 3, 4]:
                season = "dry_season"
                season_name = "Dry Season"
            else:
                season = "wet_season"
                season_name = "Wet Season"

            # Basic recommendations by season and crop
            recommendations = {
                "season": season_name,
                "month": current_month,
                "location": location or "Philippines",
                "crop_type": crop_type or "rice",
            }

            if season == "dry_season":
                if crop_type and "rice" in crop_type.lower():
                    recommendations.update(
                        {
                            "planting_advice": "Good time for dry season rice (January-February planting)",
                            "irrigation": "Ensure adequate irrigation system",
                            "pest_watch": "Monitor for rice bug, stem borer",
                            "fertilizer": "Apply complete fertilizer (14-14-14) at planting",
                        }
                    )
                else:
                    recommendations.update(
                        {
                            "planting_advice": "Good for vegetables and corn",
                            "irrigation": "Critical - ensure water supply",
                            "pest_watch": "Monitor for aphids, thrips",
                            "fertilizer": "Use organic compost and balanced NPK",
                        }
                    )
            else:  # wet_season
                if crop_type and "rice" in crop_type.lower():
                    recommendations.update(
                        {
                            "planting_advice": "Main rice season (June-July planting)",
                            "drainage": "Ensure good field drainage",
                            "pest_watch": "High risk for blast, bacterial blight",
                            "fertilizer": "Split application - basal and topdressing",
                        }
                    )
                else:
                    recommendations.update(
                        {
                            "planting_advice": "Plant flood-resistant varieties",
                            "drainage": "Critical for root crops",
                            "pest_watch": "Fungal diseases, snails",
                            "fertilizer": "Reduce nitrogen, increase potassium",
                        }
                    )

            return recommendations

        except Exception as e:
            return {"error": f"Failed to get seasonal recommendations: {str(e)}"}

    @staticmethod
    def calculate_input_needs(farm_size, crop_type="rice", season="wet"):
        """Calculate fertilizer and input needs based on farm size and crop"""
        try:
            farm_size = float(farm_size) if farm_size else 1.0

            # Basic input calculations (per hectare)
            if crop_type.lower() in ["rice", "palay"]:
                inputs = {
                    "seeds": {
                        "quantity": 40 * farm_size,  # kg per hectare
                        "unit": "kg",
                        "cost_estimate": 2000 * farm_size,
                        "notes": "Certified seeds recommended",
                    },
                    "fertilizer": {
                        "complete_fertilizer": {
                            "quantity": 2 * farm_size,  # bags per hectare
                            "unit": "bags (50kg)",
                            "type": "14-14-14 or 16-20-0",
                            "cost_estimate": 2400 * farm_size,
                        },
                        "urea": {
                            "quantity": 2 * farm_size,  # bags per hectare
                            "unit": "bags (50kg)",
                            "cost_estimate": 2200 * farm_size,
                        },
                    },
                    "pesticides": {
                        "herbicide": {
                            "cost_estimate": 1500 * farm_size,
                            "notes": "Pre-emergence and post-emergence",
                        },
                        "insecticide": {
                            "cost_estimate": 1000 * farm_size,
                            "notes": "For stem borer, rice bug",
                        },
                    },
                }
            else:  # vegetables/corn
                inputs = {
                    "seeds": {
                        "quantity": 25 * farm_size,  # kg per hectare
                        "unit": "kg",
                        "cost_estimate": 3000 * farm_size,
                    },
                    "fertilizer": {
                        "organic": {
                            "quantity": 10 * farm_size,  # bags per hectare
                            "unit": "bags (50kg)",
                            "type": "Compost or organic fertilizer",
                            "cost_estimate": 2000 * farm_size,
                        },
                        "complete_fertilizer": {
                            "quantity": 3 * farm_size,  # bags per hectare
                            "unit": "bags (50kg)",
                            "cost_estimate": 3600 * farm_size,
                        },
                    },
                }

            total_cost = sum(
                [
                    (
                        item.get("cost_estimate", 0)
                        if isinstance(item, dict)
                        else sum(
                            subitem.get("cost_estimate", 0)
                            for subitem in item.values()
                            if isinstance(subitem, dict)
                        )
                    )
                    for item in inputs.values()
                ]
            )

            return {
                "farm_size": farm_size,
                "crop_type": crop_type,
                "season": season,
                "inputs": inputs,
                "total_estimated_cost": total_cost,
                "currency": "PHP",
                "notes": "Estimates based on current market prices. Actual costs may vary.",
            }

        except Exception as e:
            return {"error": f"Failed to calculate input needs: {str(e)}"}

    @staticmethod
    def get_weather_advice(location=None):
        """Get weather-based farming advice"""
        try:
            current_month = datetime.now().month

            # Simulate weather data (in production, integrate with weather API)
            if current_month in [12, 1, 2, 3, 4]:
                weather_data = {
                    "season": "Dry Season",
                    "temperature": "25-32°C",
                    "rainfall": "Low (0-50mm/month)",
                    "humidity": "60-70%",
                    "wind": "Moderate northeast monsoon",
                }

                advice = {
                    "irrigation": "Critical - ensure adequate water supply",
                    "planting": "Good for dry season crops",
                    "pest_management": "Monitor for drought stress pests",
                    "soil_management": "Maintain soil moisture with mulching",
                }
            else:
                weather_data = {
                    "season": "Wet Season",
                    "temperature": "24-30°C",
                    "rainfall": "High (150-400mm/month)",
                    "humidity": "80-90%",
                    "wind": "Southwest monsoon",
                }

                advice = {
                    "drainage": "Ensure proper field drainage",
                    "planting": "Main season for rice",
                    "pest_management": "High risk for fungal diseases",
                    "soil_management": "Prevent waterlogging",
                }

            return {
                "location": location or "Philippines",
                "current_weather": weather_data,
                "farming_advice": advice,
                "updated": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": f"Failed to get weather advice: {str(e)}"}

    @staticmethod
    def prequalify_farmer(
        farmer_name, location, crop, land_size_ha, loan_amount_requested
    ):
        """Pre-qualify farmer for agricultural loan based on KaAni assessment"""
        try:
            land_size = float(land_size_ha) if land_size_ha else 0
            loan_amount = float(loan_amount_requested) if loan_amount_requested else 0

            # Basic pre-qualification criteria
            qualification_score = 0
            recommendations = []
            risk_factors = []

            # Land size assessment (30% weight)
            if land_size >= 2.0:
                qualification_score += 30
                recommendations.append("Good farm size for commercial production")
            elif land_size >= 1.0:
                qualification_score += 20
                recommendations.append("Adequate farm size for sustainable farming")
            elif land_size >= 0.5:
                qualification_score += 10
                recommendations.append(
                    "Small farm - consider intensive farming methods"
                )
            else:
                risk_factors.append(
                    "Very small farm size may limit production capacity"
                )

            # Crop type assessment (25% weight)
            if crop.lower() in ["rice", "palay"]:
                qualification_score += 25
                recommendations.append(
                    "Rice farming is well-supported with established markets"
                )
            elif crop.lower() in ["corn", "mais"]:
                qualification_score += 20
                recommendations.append("Corn has good market demand")
            elif crop.lower() in ["vegetables", "gulay"]:
                qualification_score += 15
                recommendations.append(
                    "Vegetable farming requires careful market timing"
                )
            else:
                qualification_score += 10
                risk_factors.append("Crop type may have limited market support")

            # Loan amount assessment (25% weight)
            expected_income_per_ha = (
                80000 if crop.lower() in ["rice", "palay"] else 60000
            )
            expected_total_income = expected_income_per_ha * land_size
            loan_to_income_ratio = (
                loan_amount / expected_total_income if expected_total_income > 0 else 1
            )

            if loan_to_income_ratio <= 0.3:
                qualification_score += 25
                recommendations.append(
                    "Conservative loan amount relative to expected income"
                )
            elif loan_to_income_ratio <= 0.5:
                qualification_score += 20
                recommendations.append("Reasonable loan amount")
            elif loan_to_income_ratio <= 0.7:
                qualification_score += 10
                recommendations.append(
                    "Moderate loan amount - ensure good crop management"
                )
            else:
                risk_factors.append("High loan amount relative to expected farm income")

            # Location assessment (20% weight)
            favorable_locations = [
                "laguna",
                "nueva ecija",
                "pangasinan",
                "iloilo",
                "camarines sur",
            ]
            if any(loc in location.lower() for loc in favorable_locations):
                qualification_score += 20
                recommendations.append("Location has good agricultural infrastructure")
            else:
                qualification_score += 10
                recommendations.append(
                    "Verify local agricultural support and market access"
                )

            # Determine status
            if qualification_score >= 70:
                status = "Pre-qualified"
                confidence_score = min(0.95, qualification_score / 100 + 0.15)
            elif qualification_score >= 50:
                status = "Needs More Info"
                confidence_score = qualification_score / 100
            else:
                status = "Not Qualified"
                confidence_score = max(0.1, qualification_score / 100)

            # Generate input recommendations
            input_recommendations = []
            if crop.lower() in ["rice", "palay"]:
                bags_14_14_14 = max(2, int(land_size * 2))
                bags_urea = max(2, int(land_size * 2))
                input_recommendations.extend(
                    [
                        f"{bags_14_14_14} bags Complete Fertilizer (14-14-14)",
                        f"{bags_urea} bags Urea (46-0-0)",
                        f"{int(land_size * 40)} kg Certified rice seeds",
                    ]
                )

            return {
                "farmer_name": farmer_name,
                "location": location,
                "crop": crop,
                "land_size_ha": land_size,
                "loan_amount_requested": loan_amount,
                "status": status,
                "qualification_score": qualification_score,
                "confidence_score": round(confidence_score, 2),
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "input_recommendations": input_recommendations,
                "next_steps": (
                    [
                        "Conduct field visit for verification",
                        "Review farmer's agricultural experience",
                        "Assess local market conditions",
                        "Calculate detailed AgScore",
                    ]
                    if status == "Pre-qualified"
                    else [
                        "Provide additional farmer information",
                        "Consider smaller loan amount",
                        "Explore alternative crops or farming methods",
                    ]
                ),
                "assessment_date": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": f"Failed to prequalify farmer: {str(e)}"}


# Function registry for KaAni
KAANI_FUNCTION_REGISTRY = {
    "get_farmer_profile": KaAniFunctions.get_farmer_profile,
    "get_farmer_orders": KaAniFunctions.get_farmer_orders,
    "get_seasonal_recommendations": KaAniFunctions.get_seasonal_recommendations,
    "calculate_input_needs": KaAniFunctions.calculate_input_needs,
    "get_weather_advice": KaAniFunctions.get_weather_advice,
    "prequalify_farmer": KaAniFunctions.prequalify_farmer,
}


def execute_kaani_function(function_name, **kwargs):
    """Execute a KaAni function by name"""
    if function_name in KAANI_FUNCTION_REGISTRY:
        return KAANI_FUNCTION_REGISTRY[function_name](**kwargs)
    else:
        return {"error": f"Function '{function_name}' not found"}

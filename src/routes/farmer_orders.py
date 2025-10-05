"""
Farmer Orders Routes for AgSense ERP
Handles order creation and management within farmer profiles
"""

from flask import Blueprint, jsonify, request

from src.routes.auth import require_permission

from ..models.farmer import Farmer
from ..models.order import Order, OrderItem
from ..models.product import Product
from ..models.user import db

farmer_orders_bp = Blueprint("farmer_orders", __name__)


@farmer_orders_bp.route("/farmers/<int:farmer_id>/orders", methods=["GET"])
@require_permission("order_management_read")
def get_farmer_orders(farmer_id):
    """Get all orders for a specific farmer"""
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        orders = Order.get_by_farmer(farmer_id)

        return jsonify(
            {
                "success": True,
                "farmer": {
                    "id": farmer.id,
                    "name": farmer.name,
                    "mobile": farmer.mobile,
                    "barangay": farmer.barangay,
                },
                "orders": [order.to_summary_dict() for order in orders],
                "total_orders": len(orders),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@farmer_orders_bp.route("/farmers/<int:farmer_id>/orders", methods=["POST"])
@require_permission("order_management_create")
def create_farmer_order(farmer_id):
    """Create a new order for a farmer"""
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        data = request.get_json()

        # Validate required fields
        if not data.get("cart_items") or len(data["cart_items"]) == 0:
            return jsonify({"success": False, "error": "Cart items are required"}), 400

        # Create new order
        order = Order(
            farmer_id=farmer_id,
            order_number=Order.generate_order_number(),
            delivery_address=data.get("delivery_address", farmer.address),
            notes=data.get("notes", ""),
            created_by=data.get("created_by", "CARD MRI Officer"),
        )

        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items
        for cart_item in data["cart_items"]:
            product = Product.query.get(cart_item["product_id"])
            if not product:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f'Product {cart_item["product_id"]} not found',
                        }
                    ),
                    400,
                )

            # Check stock availability
            if product.stock_on_hand < cart_item["quantity"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f'Insufficient stock for {product.name}. Available: {product.stock_on_hand}, Requested: {cart_item["quantity"]}',
                        }
                    ),
                    400,
                )

            order_item = OrderItem.create_from_cart_item(order.id, cart_item, product)
            db.session.add(order_item)

        # Calculate totals
        order.calculate_totals()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Order created successfully",
                "order": order.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@farmer_orders_bp.route(
    "/farmers/<int:farmer_id>/orders/<int:order_id>", methods=["GET"]
)
@require_permission("order_management_read")
def get_farmer_order_details(farmer_id, order_id):
    """Get detailed information for a specific farmer order"""
    try:
        Farmer.query.get_or_404(farmer_id)
        order = Order.query.filter_by(id=order_id, farmer_id=farmer_id).first_or_404()

        return jsonify({"success": True, "order": order.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@farmer_orders_bp.route(
    "/farmers/<int:farmer_id>/orders/<int:order_id>/status", methods=["PUT"]
)
@require_permission("order_management_update")
def update_farmer_order_status(farmer_id, order_id):
    """Update the status of a farmer's order"""
    try:
        Farmer.query.get_or_404(farmer_id)
        order = Order.query.filter_by(id=order_id, farmer_id=farmer_id).first_or_404()
        data = request.get_json()

        new_status = data.get("status")
        notes = data.get("notes")

        if not new_status:
            return jsonify({"success": False, "error": "Status is required"}), 400

        if order.update_status(new_status, notes):
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Order status updated successfully",
                    "order": order.to_summary_dict(),
                }
            )
        else:
            return jsonify({"success": False, "error": "Invalid status"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@farmer_orders_bp.route("/farmers/<int:farmer_id>/cart/validate", methods=["POST"])
@require_permission("order_management_create")
def validate_farmer_cart(farmer_id):
    """Validate cart items before order creation"""
    try:
        Farmer.query.get_or_404(farmer_id)
        data = request.get_json()
        cart_items = data.get("cart_items", [])

        if not cart_items:
            return jsonify({"success": False, "error": "Cart is empty"}), 400

        validation_results = []
        total_amount = 0
        total_cost = 0

        for item in cart_items:
            product = Product.query.get(item["product_id"])
            if not product:
                validation_results.append(
                    {
                        "product_id": item["product_id"],
                        "valid": False,
                        "error": "Product not found",
                    }
                )
                continue

            # Check stock
            if product.stock_on_hand < item["quantity"]:
                validation_results.append(
                    {
                        "product_id": item["product_id"],
                        "product_name": product.name,
                        "valid": False,
                        "error": f"Insufficient stock. Available: {product.stock_on_hand}",
                    }
                )
                continue

            # Calculate pricing
            item_total = item["quantity"] * product.selling_price
            item_cost = item["quantity"] * product.cost_price
            total_amount += item_total
            total_cost += item_cost

            validation_results.append(
                {
                    "product_id": item["product_id"],
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "quantity": item["quantity"],
                    "unit_price": product.selling_price,
                    "total_price": item_total,
                    "valid": True,
                }
            )

        # Check if all items are valid
        all_valid = all(item["valid"] for item in validation_results)

        return jsonify(
            {
                "success": True,
                "valid": all_valid,
                "items": validation_results,
                "summary": {
                    "total_amount": total_amount,
                    "total_cost": total_cost,
                    "total_margin": total_amount - total_cost,
                    "item_count": len(
                        [item for item in validation_results if item["valid"]]
                    ),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@farmer_orders_bp.route("/farmers/<int:farmer_id>/order-summary", methods=["GET"])
@require_permission("order_management_read")
def get_farmer_order_summary(farmer_id):
    """Get order summary statistics for a farmer"""
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        orders = Order.get_by_farmer(farmer_id)

        # Calculate statistics
        total_orders = len(orders)
        total_spent = sum(order.total_amount for order in orders)
        pending_orders = len([order for order in orders if order.status == "Pending"])
        completed_orders = len(
            [order for order in orders if order.status == "Delivered"]
        )

        # Recent orders (last 5)
        recent_orders = orders[:5]

        return jsonify(
            {
                "success": True,
                "farmer": {
                    "id": farmer.id,
                    "name": farmer.name,
                    "mobile": farmer.mobile,
                },
                "summary": {
                    "total_orders": total_orders,
                    "total_spent": total_spent,
                    "pending_orders": pending_orders,
                    "completed_orders": completed_orders,
                    "average_order_value": (
                        total_spent / total_orders if total_orders > 0 else 0
                    ),
                },
                "recent_orders": [order.to_summary_dict() for order in recent_orders],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

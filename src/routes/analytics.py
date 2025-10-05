from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import desc, func

from src.models.commission_payout import CommissionPayout
from src.models.farmer import Farmer
from src.models.order import Order, OrderItem, db
from src.models.partner import Partner
from src.models.product import Product
from src.routes.auth import require_permission

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/dashboard", methods=["GET"])
@require_permission("analytics_reports_read")
def get_dashboard_metrics():
    """Get main dashboard KPIs and metrics"""
    try:
        # Basic counts
        total_farmers = Farmer.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_partners = Partner.query.count()

        # Financial metrics
        total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_commissions = (
            db.session.query(func.sum(CommissionPayout.amount)).scalar() or 0
        )
        pending_commissions = (
            db.session.query(func.sum(CommissionPayout.amount))
            .filter_by(status="Pending")
            .scalar()
            or 0
        )

        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_farmers = Farmer.query.filter(
            Farmer.created_at >= thirty_days_ago
        ).count()
        recent_orders = Order.query.filter(Order.created_at >= thirty_days_ago).count()

        # Order status distribution
        order_statuses = (
            db.session.query(Order.status, func.count(Order.id).label("count"))
            .group_by(Order.status)
            .all()
        )

        # Farmer risk distribution (AgScore)
        risk_distribution = (
            db.session.query(
                Farmer.ag_score_grade, func.count(Farmer.id).label("count")
            )
            .group_by(Farmer.ag_score_grade)
            .all()
        )

        dashboard_data = {
            "overview": {
                "total_farmers": total_farmers,
                "total_products": total_products,
                "total_orders": total_orders,
                "total_partners": total_partners,
                "total_revenue": float(total_revenue),
                "total_commissions": float(total_commissions),
                "pending_commissions": float(pending_commissions),
            },
            "recent_activity": {
                "new_farmers_30d": recent_farmers,
                "new_orders_30d": recent_orders,
            },
            "order_status_distribution": [
                {"status": status, "count": count} for status, count in order_statuses
            ],
            "risk_distribution": [
                {"grade": grade or "Ungraded", "count": count}
                for grade, count in risk_distribution
            ],
        }

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/farmer-performance", methods=["GET"])
@require_permission("analytics_reports_read")
def get_farmer_performance():
    try:
        # Get farmers with their order statistics
        farmer_stats = (
            db.session.query(
                Farmer.id,
                Farmer.name,
                Farmer.location,
                Farmer.crop_type,
                Farmer.agscore,
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total_amount).label("total_spent"),
                func.avg(Order.total_amount).label("avg_order_value"),
                func.max(Order.created_at).label("last_order_date"),
            )
            .outerjoin(Order, Farmer.id == Order.farmer_id)
            .group_by(Farmer.id)
            .all()
        )

        performance_data = []
        for stat in farmer_stats:
            performance_data.append(
                {
                    "farmer_id": stat.id,
                    "name": stat.name,
                    "location": stat.location,
                    "crop_type": stat.crop_type,
                    "agscore": stat.agscore,
                    "total_orders": stat.total_orders or 0,
                    "total_spent": float(stat.total_spent or 0),
                    "avg_order_value": float(stat.avg_order_value or 0),
                    "last_order_date": (
                        stat.last_order_date.isoformat()
                        if stat.last_order_date
                        else None
                    ),
                }
            )

        return jsonify(performance_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/product-performance", methods=["GET"])
@require_permission("analytics_reports_read")
def get_product_performance():
    try:
        days = request.args.get("days", 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get product performance metrics
        product_stats = (
            db.session.query(
                Product.id,
                Product.name,
                Product.category,
                Product.brand,
                Product.selling_price,
                Product.cost_price,
                Product.margin_percentage,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.total_price).label("total_revenue"),
                func.sum(OrderItem.margin).label("total_margin"),
                func.count(func.distinct(Order.farmer_id)).label("unique_customers"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.created_at >= start_date)
            .group_by(Product.id)
            .order_by(desc("total_revenue"))
            .all()
        )

        performance_data = []
        for stat in product_stats:
            performance_data.append(
                {
                    "product_id": stat.id,
                    "name": stat.name,
                    "category": stat.category,
                    "brand": stat.brand,
                    "selling_price": float(stat.selling_price),
                    "cost_price": float(stat.cost_price),
                    "margin_percentage": float(stat.margin_percentage),
                    "total_sold": stat.total_sold,
                    "total_revenue": float(stat.total_revenue),
                    "total_margin": float(stat.total_margin),
                    "unique_customers": stat.unique_customers,
                }
            )

        return jsonify(performance_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/geographic-distribution", methods=["GET"])
@require_permission("analytics_reports_read")
def get_geographic_distribution():
    try:
        # Get farmer distribution by location
        location_stats = (
            db.session.query(
                Farmer.location,
                func.count(Farmer.id).label("farmer_count"),
                func.sum(Order.total_amount).label("total_revenue"),
                func.count(Order.id).label("total_orders"),
            )
            .outerjoin(Order, Farmer.id == Order.farmer_id)
            .group_by(Farmer.location)
            .all()
        )

        distribution_data = []
        for stat in location_stats:
            distribution_data.append(
                {
                    "location": stat.location,
                    "farmer_count": stat.farmer_count,
                    "total_revenue": float(stat.total_revenue or 0),
                    "total_orders": stat.total_orders or 0,
                    "avg_revenue_per_farmer": (
                        float((stat.total_revenue or 0) / stat.farmer_count)
                        if stat.farmer_count > 0
                        else 0
                    ),
                }
            )

        return jsonify(distribution_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/seasonal-trends", methods=["GET"])
@require_permission("analytics_reports_read")
def get_seasonal_trends():
    try:
        # Get monthly order trends for the last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)

        monthly_stats = (
            db.session.query(
                func.strftime("%Y-%m", Order.created_at).label("month"),
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("revenue"),
                func.sum(Order.total_margin).label("margin"),
                func.count(func.distinct(Order.farmer_id)).label("active_farmers"),
            )
            .filter(Order.created_at >= twelve_months_ago)
            .group_by(func.strftime("%Y-%m", Order.created_at))
            .order_by("month")
            .all()
        )

        trend_data = []
        for stat in monthly_stats:
            trend_data.append(
                {
                    "month": stat.month,
                    "order_count": stat.order_count,
                    "revenue": float(stat.revenue),
                    "margin": float(stat.margin),
                    "active_farmers": stat.active_farmers,
                }
            )

        return jsonify(trend_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/inventory-insights", methods=["GET"])
@require_permission("analytics_reports_read")
def get_inventory_insights():
    try:
        # Get inventory turnover and stock analysis
        inventory_stats = (
            db.session.query(
                Product.id,
                Product.name,
                Product.category,
                Product.stock_quantity,
                Product.low_stock_threshold,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.count(OrderItem.id).label("order_frequency"),
            )
            .outerjoin(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.id)
            .all()
        )

        insights_data = []
        for stat in inventory_stats:
            total_sold = stat.total_sold or 0
            stock_level = stat.stock_quantity
            turnover_rate = total_sold / max(stock_level, 1) if stock_level > 0 else 0

            insights_data.append(
                {
                    "product_id": stat.id,
                    "name": stat.name,
                    "category": stat.category,
                    "current_stock": stock_level,
                    "low_stock_threshold": stat.low_stock_threshold,
                    "total_sold": total_sold,
                    "order_frequency": stat.order_frequency or 0,
                    "turnover_rate": round(turnover_rate, 2),
                    "stock_status": (
                        "Low" if stock_level <= stat.low_stock_threshold else "Normal"
                    ),
                    "reorder_recommended": stock_level <= stat.low_stock_threshold,
                }
            )

        return jsonify(insights_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/partner-performance", methods=["GET"])
@require_permission("analytics_reports_read")
def get_partner_performance():
    try:
        # Get partner performance metrics
        partner_stats = (
            db.session.query(
                Partner.id,
                Partner.name,
                Partner.partner_type,
                Partner.commission_rate,
                Partner.performance_rating,
                func.count(Order.id).label("orders_handled"),
                func.sum(Order.total_amount).label("total_value"),
                func.avg(Order.total_amount).label("avg_order_value"),
            )
            .outerjoin(Order, Partner.id == Order.partner_id)
            .group_by(Partner.id)
            .all()
        )

        performance_data = []
        for stat in partner_stats:
            total_value = float(stat.total_value or 0)
            commission_earned = total_value * (stat.commission_rate / 100)

            performance_data.append(
                {
                    "partner_id": stat.id,
                    "name": stat.name,
                    "partner_type": stat.partner_type,
                    "commission_rate": stat.commission_rate,
                    "performance_rating": stat.performance_rating,
                    "orders_handled": stat.orders_handled or 0,
                    "total_value": total_value,
                    "avg_order_value": float(stat.avg_order_value or 0),
                    "commission_earned": commission_earned,
                }
            )

        return jsonify(performance_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/profitability-analysis", methods=["GET"])
@require_permission("analytics_reports_read")
def get_profitability_analysis():
    try:
        # Get detailed profitability breakdown
        profitability_stats = db.session.query(
            func.sum(Order.total_amount).label("total_revenue"),
            func.sum(Order.total_cost).label("total_cost"),
            func.sum(Order.total_margin).label("total_margin"),
            func.count(Order.id).label("total_orders"),
            func.avg(Order.total_margin).label("avg_margin_per_order"),
        ).first()

        # Get profitability by category
        category_stats = (
            db.session.query(
                Product.category,
                func.sum(OrderItem.total_price).label("revenue"),
                func.sum(OrderItem.total_cost).label("cost"),
                func.sum(OrderItem.margin).label("margin"),
                func.count(OrderItem.id).label("items_sold"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.category)
            .all()
        )

        category_breakdown = []
        for stat in category_stats:
            revenue = float(stat.revenue)
            cost = float(stat.cost)
            margin = float(stat.margin)
            margin_percentage = (margin / revenue * 100) if revenue > 0 else 0

            category_breakdown.append(
                {
                    "category": stat.category,
                    "revenue": revenue,
                    "cost": cost,
                    "margin": margin,
                    "margin_percentage": round(margin_percentage, 2),
                    "items_sold": stat.items_sold,
                }
            )

        analysis_data = {
            "overall": {
                "total_revenue": float(profitability_stats.total_revenue or 0),
                "total_cost": float(profitability_stats.total_cost or 0),
                "total_margin": float(profitability_stats.total_margin or 0),
                "total_orders": profitability_stats.total_orders or 0,
                "avg_margin_per_order": float(
                    profitability_stats.avg_margin_per_order or 0
                ),
                "overall_margin_percentage": round(
                    (
                        float(profitability_stats.total_margin or 0)
                        / float(profitability_stats.total_revenue or 1)
                        * 100
                    ),
                    2,
                ),
            },
            "by_category": category_breakdown,
        }

        return jsonify(analysis_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

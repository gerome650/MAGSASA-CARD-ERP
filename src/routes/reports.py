import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import and_, desc, func

from src.models.farmer import Farmer
from src.models.order import Order, OrderItem, db
from src.models.partner import Partner
from src.models.product import Product
from src.routes.auth import require_permission

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports/sales-summary", methods=["GET"])
@require_permission("analytics_reports_read")
def generate_sales_summary():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        format_type = request.args.get("format", "json")  # json or csv

        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        end_date = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()

        # Get sales data
        sales_data = (
            db.session.query(
                Order.id,
                Order.order_number,
                Order.created_at,
                Farmer.name.label("farmer_name"),
                Farmer.location,
                Order.total_amount,
                Order.total_cost,
                Order.total_margin,
                Order.status,
                Partner.name.label("partner_name"),
            )
            .join(Farmer, Order.farmer_id == Farmer.id)
            .outerjoin(Partner, Order.partner_id == Partner.id)
            .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
            .order_by(desc(Order.created_at))
            .all()
        )

        if format_type == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "Order ID",
                    "Order Number",
                    "Date",
                    "Farmer Name",
                    "Location",
                    "Total Amount",
                    "Total Cost",
                    "Total Margin",
                    "Status",
                    "Partner",
                ]
            )

            # Write data
            for row in sales_data:
                writer.writerow(
                    [
                        row.id,
                        row.order_number,
                        row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        row.farmer_name,
                        row.location,
                        row.total_amount,
                        row.total_cost,
                        row.total_margin,
                        row.status,
                        row.partner_name or "N/A",
                    ]
                )

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f'sales_summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv',
            )

        # Return JSON format
        summary_data = []
        total_revenue = 0
        total_margin = 0

        for row in sales_data:
            total_revenue += row.total_amount
            total_margin += row.total_margin

            summary_data.append(
                {
                    "order_id": row.id,
                    "order_number": row.order_number,
                    "date": row.created_at.isoformat(),
                    "farmer_name": row.farmer_name,
                    "location": row.location,
                    "total_amount": float(row.total_amount),
                    "total_cost": float(row.total_cost),
                    "total_margin": float(row.total_margin),
                    "status": row.status,
                    "partner_name": row.partner_name,
                }
            )

        return jsonify(
            {
                "summary": {
                    "total_orders": len(sales_data),
                    "total_revenue": total_revenue,
                    "total_margin": total_margin,
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                },
                "orders": summary_data,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/reports/inventory-report", methods=["GET"])
@require_permission("analytics_reports_read")
def generate_inventory_report():
    try:
        format_type = request.args.get("format", "json")

        # Get inventory data with sales information
        inventory_data = (
            db.session.query(
                Product.id,
                Product.name,
                Product.category,
                Product.brand,
                Product.unit,
                Product.cost_price,
                Product.selling_price,
                Product.margin_percentage,
                Product.stock_quantity,
                Product.low_stock_threshold,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.total_price).label("total_revenue"),
            )
            .outerjoin(OrderItem, Product.id == OrderItem.product_id)
            .filter(Product.is_active)
            .group_by(Product.id)
            .order_by(Product.category, Product.name)
            .all()
        )

        if format_type == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "Product ID",
                    "Name",
                    "Category",
                    "Brand",
                    "Unit",
                    "Cost Price",
                    "Selling Price",
                    "Margin %",
                    "Current Stock",
                    "Low Stock Threshold",
                    "Total Sold",
                    "Total Revenue",
                    "Stock Status",
                ]
            )

            # Write data
            for row in inventory_data:
                stock_status = (
                    "Low Stock"
                    if row.stock_quantity <= row.low_stock_threshold
                    else "Normal"
                )
                writer.writerow(
                    [
                        row.id,
                        row.name,
                        row.category,
                        row.brand or "N/A",
                        row.unit,
                        row.cost_price,
                        row.selling_price,
                        row.margin_percentage,
                        row.stock_quantity,
                        row.low_stock_threshold,
                        row.total_sold or 0,
                        row.total_revenue or 0,
                        stock_status,
                    ]
                )

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.csv',
            )

        # Return JSON format
        report_data = []
        low_stock_count = 0
        total_inventory_value = 0

        for row in inventory_data:
            stock_status = (
                "Low Stock"
                if row.stock_quantity <= row.low_stock_threshold
                else "Normal"
            )
            if stock_status == "Low Stock":
                low_stock_count += 1

            inventory_value = row.stock_quantity * row.cost_price
            total_inventory_value += inventory_value

            report_data.append(
                {
                    "product_id": row.id,
                    "name": row.name,
                    "category": row.category,
                    "brand": row.brand,
                    "unit": row.unit,
                    "cost_price": float(row.cost_price),
                    "selling_price": float(row.selling_price),
                    "margin_percentage": float(row.margin_percentage),
                    "stock_quantity": row.stock_quantity,
                    "low_stock_threshold": row.low_stock_threshold,
                    "total_sold": row.total_sold or 0,
                    "total_revenue": float(row.total_revenue or 0),
                    "stock_status": stock_status,
                    "inventory_value": inventory_value,
                }
            )

        return jsonify(
            {
                "summary": {
                    "total_products": len(report_data),
                    "low_stock_items": low_stock_count,
                    "total_inventory_value": total_inventory_value,
                    "report_date": datetime.now().isoformat(),
                },
                "products": report_data,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/reports/farmer-analysis", methods=["GET"])
@require_permission("analytics_reports_read")
def generate_farmer_analysis():
    try:
        format_type = request.args.get("format", "json")

        # Get farmer data with order statistics
        farmer_data = (
            db.session.query(
                Farmer.id,
                Farmer.name,
                Farmer.location,
                Farmer.barangay,
                Farmer.crop_type,
                Farmer.land_size_ha,
                Farmer.agscore,
                Farmer.loan_status,
                Farmer.loan_amount,
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total_amount).label("total_spent"),
                func.avg(Order.total_amount).label("avg_order_value"),
                func.max(Order.created_at).label("last_order_date"),
            )
            .outerjoin(Order, Farmer.id == Order.farmer_id)
            .group_by(Farmer.id)
            .order_by(Farmer.location, Farmer.name)
            .all()
        )

        if format_type == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "Farmer ID",
                    "Name",
                    "Location",
                    "Barangay",
                    "Crop Type",
                    "Land Size (ha)",
                    "AgScore",
                    "Loan Status",
                    "Loan Amount",
                    "Total Orders",
                    "Total Spent",
                    "Avg Order Value",
                    "Last Order Date",
                ]
            )

            # Write data
            for row in farmer_data:
                writer.writerow(
                    [
                        row.id,
                        row.name,
                        row.location,
                        row.barangay,
                        row.crop_type,
                        row.land_size_ha,
                        row.agscore or "N/A",
                        row.loan_status,
                        row.loan_amount or 0,
                        row.total_orders or 0,
                        row.total_spent or 0,
                        row.avg_order_value or 0,
                        (
                            row.last_order_date.strftime("%Y-%m-%d")
                            if row.last_order_date
                            else "Never"
                        ),
                    ]
                )

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f'farmer_analysis_{datetime.now().strftime("%Y%m%d")}.csv',
            )

        # Return JSON format
        analysis_data = []
        total_farmers = len(farmer_data)
        active_farmers = 0
        total_land_size = 0

        for row in farmer_data:
            if row.total_orders and row.total_orders > 0:
                active_farmers += 1

            total_land_size += row.land_size_ha

            analysis_data.append(
                {
                    "farmer_id": row.id,
                    "name": row.name,
                    "location": row.location,
                    "barangay": row.barangay,
                    "crop_type": row.crop_type,
                    "land_size_ha": float(row.land_size_ha),
                    "agscore": row.agscore,
                    "loan_status": row.loan_status,
                    "loan_amount": float(row.loan_amount or 0),
                    "total_orders": row.total_orders or 0,
                    "total_spent": float(row.total_spent or 0),
                    "avg_order_value": float(row.avg_order_value or 0),
                    "last_order_date": (
                        row.last_order_date.isoformat() if row.last_order_date else None
                    ),
                }
            )

        return jsonify(
            {
                "summary": {
                    "total_farmers": total_farmers,
                    "active_farmers": active_farmers,
                    "total_land_size": total_land_size,
                    "avg_land_size": (
                        total_land_size / total_farmers if total_farmers > 0 else 0
                    ),
                    "report_date": datetime.now().isoformat(),
                },
                "farmers": analysis_data,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/reports/financial-summary", methods=["GET"])
@require_permission("analytics_reports_read")
def generate_financial_summary():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        end_date = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()

        # Get financial summary
        financial_stats = (
            db.session.query(
                func.sum(Order.total_amount).label("total_revenue"),
                func.sum(Order.total_cost).label("total_cost"),
                func.sum(Order.total_margin).label("total_margin"),
                func.count(Order.id).label("total_orders"),
                func.avg(Order.total_amount).label("avg_order_value"),
            )
            .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
            .first()
        )

        # Get daily breakdown
        daily_stats = (
            db.session.query(
                func.date(Order.created_at).label("date"),
                func.sum(Order.total_amount).label("revenue"),
                func.sum(Order.total_margin).label("margin"),
                func.count(Order.id).label("orders"),
            )
            .filter(and_(Order.created_at >= start_date, Order.created_at <= end_date))
            .group_by(func.date(Order.created_at))
            .order_by("date")
            .all()
        )

        daily_breakdown = []
        for stat in daily_stats:
            daily_breakdown.append(
                {
                    "date": stat.date.isoformat(),
                    "revenue": float(stat.revenue),
                    "margin": float(stat.margin),
                    "orders": stat.orders,
                }
            )

        summary_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_revenue": float(financial_stats.total_revenue or 0),
                "total_cost": float(financial_stats.total_cost or 0),
                "total_margin": float(financial_stats.total_margin or 0),
                "total_orders": financial_stats.total_orders or 0,
                "avg_order_value": float(financial_stats.avg_order_value or 0),
                "margin_percentage": round(
                    (
                        float(financial_stats.total_margin or 0)
                        / float(financial_stats.total_revenue or 1)
                        * 100
                    ),
                    2,
                ),
            },
            "daily_breakdown": daily_breakdown,
        }

        return jsonify(summary_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

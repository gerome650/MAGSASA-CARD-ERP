from flask import Blueprint, request, jsonify
from src.models.user import db
from src.routes.auth import require_permission, require_auth
from src.models.farmer import Farmer
from src.models.product import Product
from src.models.order import Order
from src.models.partner import Partner
from src.models.commission_payout import CommissionPayout
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, extract
import json

financial_bp = Blueprint('financial', __name__)

@financial_bp.route('/financial/dashboard', methods=['GET'])
@require_permission('financial_reports_read')
def get_financial_dashboard():
    """Get main financial dashboard KPIs and metrics"""
    try:
        # Basic financial metrics
        total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_cost = db.session.query(func.sum(Order.total_amount * 0.7)).scalar() or 0  # Assuming 70% cost ratio
        gross_profit = total_revenue - total_cost
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Commission metrics
        total_commissions_paid = db.session.query(func.sum(CommissionPayout.amount)).filter_by(status='Paid').scalar() or 0
        pending_commissions = db.session.query(func.sum(CommissionPayout.amount)).filter_by(status='Pending').scalar() or 0
        
        # Monthly metrics (current month)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= current_month_start).scalar() or 0
        monthly_orders = Order.query.filter(Order.created_at >= current_month_start).count()
        
        # Year-to-date metrics
        year_start = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        ytd_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= year_start).scalar() or 0
        ytd_orders = Order.query.filter(Order.created_at >= year_start).count()
        
        # Average order value
        avg_order_value = total_revenue / Order.query.count() if Order.query.count() > 0 else 0
        
        # Top revenue generating farmers
        top_farmers = db.session.query(
            Farmer.name,
            func.sum(Order.total_amount).label('total_spent')
        ).join(Order, Farmer.id == Order.farmer_id).group_by(Farmer.id).order_by(func.sum(Order.total_amount).desc()).limit(5).all()
        
        dashboard_data = {
            'overview': {
                'total_revenue': float(total_revenue),
                'total_cost': float(total_cost),
                'gross_profit': float(gross_profit),
                'gross_margin_percentage': round(gross_margin, 2),
                'total_commissions_paid': float(total_commissions_paid),
                'pending_commissions': float(pending_commissions),
                'avg_order_value': float(avg_order_value)
            },
            'monthly_metrics': {
                'revenue': float(monthly_revenue),
                'orders': monthly_orders
            },
            'ytd_metrics': {
                'revenue': float(ytd_revenue),
                'orders': ytd_orders
            },
            'top_farmers': [
                {
                    'name': name,
                    'total_spent': float(total_spent)
                } for name, total_spent in top_farmers
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/profit-loss', methods=['GET'])
@require_permission('financial_reports_read')
def get_profit_loss_statement():
    """Generate Profit & Loss statement for a given period"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Revenue calculation
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= start_dt, Order.created_at <= end_dt)
        ).scalar() or 0
        
        # Cost of Goods Sold (COGS) - simplified calculation
        # In a real scenario, this would be based on actual product costs
        total_cogs = total_revenue * 0.65  # Assuming 65% COGS
        
        # Gross Profit
        gross_profit = total_revenue - total_cogs
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Operating Expenses (estimated)
        commission_expenses = db.session.query(func.sum(CommissionPayout.amount)).filter(
            and_(CommissionPayout.created_at >= start_dt, CommissionPayout.created_at <= end_dt)
        ).scalar() or 0
        
        # Estimated operating expenses (would be actual in real implementation)
        estimated_salaries = 50000  # Monthly salary expenses
        estimated_marketing = 10000  # Monthly marketing expenses
        estimated_operations = 15000  # Monthly operational expenses
        
        total_operating_expenses = commission_expenses + estimated_salaries + estimated_marketing + estimated_operations
        
        # Operating Income
        operating_income = gross_profit - total_operating_expenses
        operating_margin = (operating_income / total_revenue * 100) if total_revenue > 0 else 0
        
        # Net Income (simplified - no taxes, interest, etc.)
        net_income = operating_income
        net_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
        
        pl_statement = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total_revenue': float(total_revenue)
            },
            'cost_of_goods_sold': {
                'total_cogs': float(total_cogs)
            },
            'gross_profit': {
                'amount': float(gross_profit),
                'margin_percentage': round(gross_margin, 2)
            },
            'operating_expenses': {
                'commission_expenses': float(commission_expenses),
                'salary_expenses': float(estimated_salaries),
                'marketing_expenses': float(estimated_marketing),
                'operational_expenses': float(estimated_operations),
                'total_operating_expenses': float(total_operating_expenses)
            },
            'operating_income': {
                'amount': float(operating_income),
                'margin_percentage': round(operating_margin, 2)
            },
            'net_income': {
                'amount': float(net_income),
                'margin_percentage': round(net_margin, 2)
            }
        }
        
        return jsonify(pl_statement)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/revenue-analysis', methods=['GET'])
@require_permission('financial_reports_read')
def get_revenue_analysis():
    """Get detailed revenue analysis by various dimensions"""
    try:
        # Revenue by month (last 12 months)
        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_revenue = db.session.query(
            func.strftime('%Y-%m', Order.created_at).label('month'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).filter(Order.created_at >= twelve_months_ago).group_by(func.strftime('%Y-%m', Order.created_at)).all()
        
        # Revenue by product category
        revenue_by_category = db.session.query(
            Product.category,
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('order_count')
        ).join(Order, Product.id == Order.product_id).group_by(Product.category).all()
        
        # Revenue by farmer location
        revenue_by_location = db.session.query(
            Farmer.barangay,
            func.sum(Order.total_amount).label('revenue'),
            func.count(func.distinct(Farmer.id)).label('farmer_count'),
            func.count(Order.id).label('order_count')
        ).join(Order, Farmer.id == Order.farmer_id).group_by(Farmer.barangay).order_by(func.sum(Order.total_amount).desc()).limit(10).all()
        
        # Top performing products by revenue
        top_products = db.session.query(
            Product.name,
            Product.category,
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).join(Order, Product.id == Order.product_id).group_by(Product.id).order_by(func.sum(Order.total_amount).desc()).limit(10).all()
        
        revenue_analysis = {
            'monthly_revenue': [
                {
                    'month': month,
                    'revenue': float(revenue or 0),
                    'order_count': order_count,
                    'avg_order_value': float(avg_order_value or 0)
                } for month, revenue, order_count, avg_order_value in monthly_revenue
            ],
            'revenue_by_category': [
                {
                    'category': category or 'Uncategorized',
                    'revenue': float(revenue or 0),
                    'order_count': order_count
                } for category, revenue, order_count in revenue_by_category
            ],
            'revenue_by_location': [
                {
                    'location': location or 'Unknown',
                    'revenue': float(revenue or 0),
                    'farmer_count': farmer_count,
                    'order_count': order_count
                } for location, revenue, farmer_count, order_count in revenue_by_location
            ],
            'top_products': [
                {
                    'product_name': name,
                    'category': category,
                    'revenue': float(revenue or 0),
                    'order_count': order_count,
                    'avg_order_value': float(avg_order_value or 0)
                } for name, category, revenue, order_count, avg_order_value in top_products
            ]
        }
        
        return jsonify(revenue_analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/margin-analysis', methods=['GET'])
@require_permission('financial_reports_read')
def get_margin_analysis():
    """Get detailed margin analysis by products and categories"""
    try:
        # Margin analysis by product
        product_margins = db.session.query(
            Product.name,
            Product.category,
            Product.cost_price,
            Product.selling_price,
            func.count(Order.id).label('units_sold'),
            func.sum(Order.total_amount).label('total_revenue')
        ).join(Order, Product.id == Order.product_id).group_by(Product.id).all()
        
        # Calculate detailed margins
        margin_data = []
        for name, category, cost, selling, units, revenue in product_margins:
            if selling and cost:
                unit_margin = selling - cost
                margin_percentage = (unit_margin / selling * 100)
                total_cost = cost * units
                total_margin = (revenue or 0) - total_cost
            else:
                unit_margin = 0
                margin_percentage = 0
                total_cost = 0
                total_margin = 0
            
            margin_data.append({
                'product_name': name,
                'category': category,
                'cost_price': float(cost or 0),
                'selling_price': float(selling or 0),
                'unit_margin': float(unit_margin),
                'margin_percentage': round(margin_percentage, 2),
                'units_sold': units,
                'total_revenue': float(revenue or 0),
                'total_cost': float(total_cost),
                'total_margin': float(total_margin)
            })
        
        # Margin analysis by category
        category_margins = {}
        for item in margin_data:
            category = item['category']
            if category not in category_margins:
                category_margins[category] = {
                    'total_revenue': 0,
                    'total_cost': 0,
                    'total_margin': 0,
                    'product_count': 0
                }
            
            category_margins[category]['total_revenue'] += item['total_revenue']
            category_margins[category]['total_cost'] += item['total_cost']
            category_margins[category]['total_margin'] += item['total_margin']
            category_margins[category]['product_count'] += 1
        
        # Calculate category margin percentages
        category_analysis = []
        for category, data in category_margins.items():
            margin_percentage = (data['total_margin'] / data['total_revenue'] * 100) if data['total_revenue'] > 0 else 0
            category_analysis.append({
                'category': category,
                'total_revenue': data['total_revenue'],
                'total_cost': data['total_cost'],
                'total_margin': data['total_margin'],
                'margin_percentage': round(margin_percentage, 2),
                'product_count': data['product_count']
            })
        
        margin_analysis = {
            'product_margins': margin_data,
            'category_margins': category_analysis
        }
        
        return jsonify(margin_analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/cash-flow', methods=['GET'])
@require_permission('financial_reports_read')
def get_cash_flow_analysis():
    """Get cash flow analysis and projections"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Operating Activities
        cash_from_sales = db.session.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= start_dt, Order.created_at <= end_dt)
        ).scalar() or 0
        
        commission_payments = db.session.query(func.sum(CommissionPayout.amount)).filter(
            and_(CommissionPayout.created_at >= start_dt, CommissionPayout.created_at <= end_dt, CommissionPayout.status == 'Paid')
        ).scalar() or 0
        
        # Estimated operating expenses
        estimated_operating_expenses = 75000  # Monthly operating expenses
        
        net_cash_from_operations = cash_from_sales - commission_payments - estimated_operating_expenses
        
        # Investing Activities (simplified)
        capital_expenditures = 0  # Would be actual CapEx in real implementation
        net_cash_from_investing = -capital_expenditures
        
        # Financing Activities (simplified)
        loan_proceeds = 0  # Would be actual loan proceeds
        loan_payments = 0  # Would be actual loan payments
        net_cash_from_financing = loan_proceeds - loan_payments
        
        # Net Cash Flow
        net_cash_flow = net_cash_from_operations + net_cash_from_investing + net_cash_from_financing
        
        # Daily cash flow for the period
        daily_cash_flow = []
        current_date = start_dt
        while current_date <= end_dt:
            daily_sales = db.session.query(func.sum(Order.total_amount)).filter(
                func.date(Order.created_at) == current_date.date()
            ).scalar() or 0
            
            daily_cash_flow.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'cash_inflow': float(daily_sales),
                'cash_outflow': float(daily_sales * 0.1),  # Simplified outflow calculation
                'net_cash_flow': float(daily_sales * 0.9)
            })
            
            current_date += timedelta(days=1)
        
        cash_flow_data = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'operating_activities': {
                'cash_from_sales': float(cash_from_sales),
                'commission_payments': float(commission_payments),
                'operating_expenses': float(estimated_operating_expenses),
                'net_cash_from_operations': float(net_cash_from_operations)
            },
            'investing_activities': {
                'capital_expenditures': float(capital_expenditures),
                'net_cash_from_investing': float(net_cash_from_investing)
            },
            'financing_activities': {
                'loan_proceeds': float(loan_proceeds),
                'loan_payments': float(loan_payments),
                'net_cash_from_financing': float(net_cash_from_financing)
            },
            'net_cash_flow': float(net_cash_flow),
            'daily_cash_flow': daily_cash_flow
        }
        
        return jsonify(cash_flow_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/kpis', methods=['GET'])
@require_permission('financial_reports_read')
def get_financial_kpis():
    """Get key financial performance indicators and ratios"""
    try:
        # Basic financial data
        total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_orders = Order.query.count()
        total_farmers = Farmer.query.count()
        
        # Calculate KPIs
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        revenue_per_farmer = total_revenue / total_farmers if total_farmers > 0 else 0
        
        # Monthly growth rate (simplified)
        current_month_start = datetime.now().replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= current_month_start).scalar() or 0
        last_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= last_month_start, Order.created_at < current_month_start)
        ).scalar() or 0
        
        monthly_growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
        
        # Customer metrics
        repeat_customers = db.session.query(func.count(func.distinct(Order.farmer_id))).filter(
            Order.farmer_id.in_(
                db.session.query(Order.farmer_id).group_by(Order.farmer_id).having(func.count(Order.id) > 1)
            )
        ).scalar() or 0
        
        customer_retention_rate = (repeat_customers / total_farmers * 100) if total_farmers > 0 else 0
        
        # Inventory turnover (simplified)
        total_inventory_value = db.session.query(func.sum(Product.stock_quantity * Product.cost_price)).scalar() or 0
        total_cogs = total_revenue * 0.65  # Simplified COGS calculation
        inventory_turnover = total_cogs / total_inventory_value if total_inventory_value > 0 else 0
        
        kpis = {
            'revenue_metrics': {
                'total_revenue': float(total_revenue),
                'avg_order_value': float(avg_order_value),
                'revenue_per_farmer': float(revenue_per_farmer),
                'monthly_growth_rate': round(monthly_growth_rate, 2)
            },
            'customer_metrics': {
                'total_farmers': total_farmers,
                'repeat_customers': repeat_customers,
                'customer_retention_rate': round(customer_retention_rate, 2)
            },
            'operational_metrics': {
                'total_orders': total_orders,
                'inventory_turnover': round(inventory_turnover, 2)
            },
            'profitability_metrics': {
                'gross_margin_percentage': 35.0,  # Simplified calculation
                'operating_margin_percentage': 15.0,  # Simplified calculation
                'net_margin_percentage': 12.0  # Simplified calculation
            }
        }
        
        return jsonify(kpis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@financial_bp.route('/financial/export/<report_type>', methods=['GET'])
@require_permission('financial_reports_read')
def export_financial_report(report_type):
    """Export financial reports in CSV format"""
    try:
        if report_type == 'profit-loss':
            data = get_profit_loss_statement().get_json()
        elif report_type == 'revenue-analysis':
            data = get_revenue_analysis().get_json()
        elif report_type == 'margin-analysis':
            data = get_margin_analysis().get_json()
        elif report_type == 'cash-flow':
            data = get_cash_flow_analysis().get_json()
        elif report_type == 'kpis':
            data = get_financial_kpis().get_json()
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Convert to CSV format (simplified)
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data based on report type
        if report_type == 'profit-loss':
            writer.writerow(['Financial Statement', 'Amount'])
            writer.writerow(['Total Revenue', data['revenue']['total_revenue']])
            writer.writerow(['Total COGS', data['cost_of_goods_sold']['total_cogs']])
            writer.writerow(['Gross Profit', data['gross_profit']['amount']])
            writer.writerow(['Operating Expenses', data['operating_expenses']['total_operating_expenses']])
            writer.writerow(['Net Income', data['net_income']['amount']])
        
        csv_data = output.getvalue()
        output.close()
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=agsense_{report_type}_report.csv'
        }
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


from flask import Blueprint, request, jsonify
from src.models.order import Order, OrderItem, db
from src.models.product import Product
from src.models.farmer import Farmer
from datetime import datetime
import uuid
from src.routes.auth import require_permission, require_auth

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        farmer_id = request.args.get('farmer_id', type=int)
        
        query = Order.query
        
        if status:
            query = query.filter_by(status=status)
        
        if farmer_id:
            query = query.filter_by(farmer_id=farmer_id)
        
        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': orders.total,
            'pages': orders.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@require_permission('order_management_read')
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify(order.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders', methods=['POST'])
@require_permission('order_management_create')
def create_order():
    try:
        data = request.get_json()
        
        # Validate farmer exists
        farmer = Farmer.query.get(data['farmer_id'])
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create order
        order = Order(
            order_number=order_number,
            farmer_id=data['farmer_id'],
            delivery_address=data.get('delivery_address'),
            notes=data.get('notes')
        )
        
        total_amount = 0
        total_cost = 0
        total_margin = 0
        
        # Process order items
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                return jsonify({'error': f'Product {item_data["product_id"]} not found'}), 404
            
            quantity = item_data['quantity']
            unit_price = product.selling_price
            unit_cost = product.cost_price
            item_total_price = quantity * unit_price
            item_total_cost = quantity * unit_cost
            item_margin = item_total_price - item_total_cost
            
            order_item = OrderItem(
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=unit_cost,
                total_price=item_total_price,
                total_cost=item_total_cost,
                margin=item_margin
            )
            
            order.order_items.append(order_item)
            
            total_amount += item_total_price
            total_cost += item_total_cost
            total_margin += item_margin
            
            # Update product stock
            product.stock_quantity -= quantity
        
        order.total_amount = total_amount
        order.total_cost = total_cost
        order.total_margin = total_margin
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify(order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
@require_permission('order_management_update')
def update_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        order.status = data.get('status', order.status)
        order.payment_status = data.get('payment_status', order.payment_status)
        order.delivery_address = data.get('delivery_address', order.delivery_address)
        order.delivery_date = datetime.fromisoformat(data['delivery_date']) if data.get('delivery_date') else order.delivery_date
        order.partner_id = data.get('partner_id', order.partner_id)
        order.notes = data.get('notes', order.notes)
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@require_permission('order_management_update')
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        order.status = data['status']
        order.updated_at = datetime.utcnow()
        
        # If delivered, set delivery date
        if data['status'] == 'Delivered' and not order.delivery_date:
            order.delivery_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


"""
Product Routes for AgSense ERP Product Catalog
Comprehensive product management with inventory, pricing, and supplier integration
"""

from flask import Blueprint, request, jsonify
from ..models.user import db
from ..models.product import Product
from ..models.category import Category
from ..models.supplier import Supplier
from src.routes.auth import require_permission, require_auth

product_bp = Blueprint('product', __name__)


@product_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering and pagination"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category_id = request.args.get('category_id')
        supplier_id = request.args.get('supplier_id')
        status = request.args.get('status')
        search = request.args.get('search')
        stock_status = request.args.get('stock_status')

        query = Product.query

        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)

        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)

        if status:
            query = query.filter_by(status=status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                    Product.brand.ilike(search_pattern)
                )
            )

        if stock_status:
            if stock_status == 'low_stock':
                query = query.filter(Product.stock_on_hand <= Product.reorder_point)
            elif stock_status == 'out_of_stock':
                query = query.filter(Product.stock_on_hand <= 0)
            elif stock_status == 'in_stock':
                query = query.filter(Product.stock_on_hand > Product.reorder_point)

        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        products = pagination.items

        return jsonify({
            'products': [product.to_dict() for product in products],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/<int:product_id>', methods=['GET'])
@require_permission('product_catalog_read')
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products', methods=['POST'])
@require_permission('product_catalog_create')
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['sku', 'name', 'category_id', 'supplier_id', 'uom', 'cost_price', 'selling_price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        # Check if SKU already exists
        existing = Product.query.filter_by(sku=data['sku']).first()
        if existing:
            return jsonify({'error': 'SKU already exists'}), 400

        # Validate category and supplier exist
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Invalid category ID'}), 400

        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'error': 'Invalid supplier ID'}), 400

        product = Product(
            sku=data['sku'],
            name=data['name'],
            description=data.get('description'),
            brand=data.get('brand'),
            category_id=data['category_id'],
            uom=data['uom'],
            unit_value=data.get('unit_value'),
            image_url=data.get('image_url'),
            thumbnail_url=data.get('thumbnail_url'),
            image_filename=data.get('image_filename'),
            status=data.get('status', 'Active'),
            supplier_id=data['supplier_id'],
            cost_price=data['cost_price'],
            selling_price=data['selling_price'],
            stock_on_hand=data.get('stock_on_hand', 0),
            reorder_point=data.get('reorder_point', 10),
            composition=data.get('composition'),
            application_rate=data.get('application_rate'),
            crop_suitability=data.get('crop_suitability'),
            season_suitability=data.get('season_suitability')
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@require_permission('product_catalog_update')
def update_product(product_id):
    """Update an existing product"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()

        # Check if SKU is being changed and if it already exists
        if 'sku' in data and data['sku'] != product.sku:
            existing = Product.query.filter_by(sku=data['sku']).first()
            if existing:
                return jsonify({'error': 'SKU already exists'}), 400

        # Validate category and supplier if being updated
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({'error': 'Invalid category ID'}), 400

        if 'supplier_id' in data:
            supplier = Supplier.query.get(data['supplier_id'])
            if not supplier:
                return jsonify({'error': 'Invalid supplier ID'}), 400

        # Update fields
        updatable_fields = [
            'sku', 'name', 'description', 'brand', 'category_id', 'uom',
            'unit_value', 'image_url', 'thumbnail_url', 'image_filename', 'status', 'supplier_id', 'cost_price',
            'selling_price', 'stock_on_hand', 'reorder_point', 'composition',
            'application_rate', 'crop_suitability', 'season_suitability'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])

        db.session.commit()

        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_permission('product_catalog_delete')
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get_or_404(product_id)

        # Check if product has orders (future enhancement)
        # if product.order_items:
        #     return jsonify({'error': 'Cannot delete product with existing orders'}), 400

        db.session.delete(product)
        db.session.commit()

        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/<int:product_id>/stock', methods=['PUT'])
@require_permission('product_catalog_update')
def update_stock(product_id):
    """Update product stock quantity"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()

        if 'quantity_change' not in data:
            return jsonify({'error': 'quantity_change is required'}), 400

        quantity_change = int(data['quantity_change'])
        reason = data.get('reason', 'Manual Adjustment')

        new_stock = product.update_stock(quantity_change, reason)
        db.session.commit()

        return jsonify({
            'message': 'Stock updated successfully',
            'new_stock': new_stock,
            'stock_status': product.get_stock_status()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/low-stock', methods=['GET'])
@require_permission('product_catalog_read')
def get_low_stock_products():
    """Get products with low stock levels"""
    try:
        products = Product.get_low_stock_products()
        return jsonify({
            'products': [product.to_dict() for product in products],
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/search', methods=['GET'])
@require_permission('product_catalog_read')
def search_products():
    """Search products by name, SKU, or brand"""
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400

        products = Product.search_products(search_term)
        return jsonify({
            'products': [product.to_dict() for product in products],
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/by-category/<int:category_id>', methods=['GET'])
@require_permission('product_catalog_read')
def get_products_by_category(category_id):
    """Get products by category"""
    try:
        products = Product.get_by_category(category_id)
        return jsonify({
            'products': [product.to_dict() for product in products],
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@product_bp.route('/products/by-supplier/<int:supplier_id>', methods=['GET'])
@require_permission('product_catalog_read')
def get_products_by_supplier(supplier_id):
    """Get products by supplier"""
    try:
        products = Product.get_by_supplier(supplier_id)
        return jsonify({
            'products': [product.to_dict() for product in products],
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

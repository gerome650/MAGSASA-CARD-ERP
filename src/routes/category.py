"""
Category Routes for AgSense ERP Product Catalog
Handles CRUD operations for product categories
"""

from flask import Blueprint, request, jsonify
from ..models.user import db
from ..models.category import Category
from src.routes.auth import require_permission, require_auth

category_bp = Blueprint('category', __name__)

@category_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with optional filtering"""
    try:
        parent_id = request.args.get('parent_id')
        
        if parent_id is not None:
            # Get subcategories for a specific parent
            if parent_id == '':
                # Get main categories (no parent)
                categories = Category.get_main_categories()
            else:
                categories = Category.get_subcategories(int(parent_id))
        else:
            # Get all categories
            categories = Category.query.all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories],
            'total': len(categories)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@category_bp.route('/categories/<int:category_id>', methods=['GET'])
@require_permission('product_catalog_read')
def get_category(category_id):
    """Get a specific category by ID"""
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify(category.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@category_bp.route('/categories', methods=['POST'])
@require_permission('product_catalog_create')
def create_category():
    """Create a new category"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Category name is required'}), 400
        
        # Check if category name already exists
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Category name already exists'}), 400
        
        category = Category(
            name=data['name'],
            parent_id=data.get('parent_id'),
            description=data.get('description')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': category.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@require_permission('product_catalog_update')
def update_category(category_id):
    """Update an existing category"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            # Check if new name already exists (excluding current category)
            existing = Category.query.filter(
                Category.name == data['name'],
                Category.id != category_id
            ).first()
            if existing:
                return jsonify({'error': 'Category name already exists'}), 400
            category.name = data['name']
        
        if 'parent_id' in data:
            category.parent_id = data['parent_id']
        
        if 'description' in data:
            category.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Category updated successfully',
            'category': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@require_permission('product_catalog_delete')
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Check if category has products
        if category.products:
            return jsonify({
                'error': 'Cannot delete category with existing products'
            }), 400
        
        # Check if category has subcategories
        if category.subcategories:
            return jsonify({
                'error': 'Cannot delete category with subcategories'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@category_bp.route('/categories/tree', methods=['GET'])
@require_permission('product_catalog_read')
def get_category_tree():
    """Get categories in a hierarchical tree structure"""
    try:
        def build_tree(parent_id=None):
            categories = Category.query.filter_by(parent_id=parent_id).all()
            tree = []
            for category in categories:
                node = category.to_dict()
                node['children'] = build_tree(category.id)
                tree.append(node)
            return tree
        
        tree = build_tree()
        return jsonify({'category_tree': tree})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


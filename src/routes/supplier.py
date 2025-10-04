"""
Supplier Routes for AgSense ERP Product Catalog
Handles CRUD operations for suppliers
"""

from flask import Blueprint, request, jsonify
from ..models.user import db
from ..models.supplier import Supplier
from src.routes.auth import require_permission, require_auth

supplier_bp = Blueprint('supplier', __name__)


@supplier_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers with optional filtering"""
    try:
        status = request.args.get('status')
        search = request.args.get('search')

        query = Supplier.query

        if status:
            query = query.filter_by(status=status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Supplier.name.ilike(search_pattern),
                    Supplier.contact_person.ilike(search_pattern),
                    Supplier.email.ilike(search_pattern)
                )
            )

        suppliers = query.all()

        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers],
            'total': len(suppliers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
@require_permission('product_catalog_read')
def get_supplier(supplier_id):
    """Get a specific supplier by ID"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        supplier_data = supplier.to_dict()
        supplier_data['product_count'] = supplier.get_product_count()
        return jsonify(supplier_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@supplier_bp.route('/suppliers', methods=['POST'])
@require_permission('product_catalog_create')
def create_supplier():
    """Create a new supplier"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Supplier name is required'}), 400

        supplier = Supplier(
            name=data['name'],
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            website=data.get('website'),
            tax_id=data.get('tax_id'),
            payment_terms=data.get('payment_terms'),
            status=data.get('status', 'Active'),
            notes=data.get('notes')
        )

        db.session.add(supplier)
        db.session.commit()

        return jsonify({
            'message': 'Supplier created successfully',
            'supplier': supplier.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@require_permission('product_catalog_update')
def update_supplier(supplier_id):
    """Update an existing supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()

        # Update fields
        for field in ['name', 'contact_person', 'email', 'phone', 'address',
                      'website', 'tax_id', 'payment_terms', 'status', 'notes']:
            if field in data:
                setattr(supplier, field, data[field])

        db.session.commit()

        return jsonify({
            'message': 'Supplier updated successfully',
            'supplier': supplier.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@require_permission('product_catalog_delete')
def delete_supplier(supplier_id):
    """Delete a supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)

        # Check if supplier has products
        if supplier.get_product_count() > 0:
            return jsonify({
                'error': 'Cannot delete supplier with existing products'
            }), 400

        db.session.delete(supplier)
        db.session.commit()

        return jsonify({'message': 'Supplier deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@supplier_bp.route('/suppliers/active', methods=['GET'])
@require_permission('product_catalog_read')
def get_active_suppliers():
    """Get all active suppliers for dropdown lists"""
    try:
        suppliers = Supplier.get_active_suppliers()
        return jsonify({
            'suppliers': [{'id': s.id, 'name': s.name} for s in suppliers]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

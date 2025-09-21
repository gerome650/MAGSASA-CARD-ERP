from flask import Blueprint, request, jsonify
from src.models.partner import Partner, db
from datetime import datetime
from src.routes.auth import require_permission, require_auth

partner_bp = Blueprint('partner', __name__)

@partner_bp.route('/partners', methods=['GET'])
def get_partners():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        partner_type = request.args.get('type', '')
        
        query = Partner.query.filter_by(status='Active')
        
        if search:
            query = query.filter(
                (Partner.name.contains(search)) |
                (Partner.contact_person.contains(search))
            )
        
        if partner_type:
            query = query.filter_by(partner_type=partner_type)
        
        partners = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'partners': [partner.to_dict() for partner in partners.items],
            'total': partners.total,
            'pages': partners.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@partner_bp.route('/partners/<int:partner_id>', methods=['GET'])
@require_permission('partner_network_read')
def get_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        return jsonify(partner.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@partner_bp.route('/partners', methods=['POST'])
@require_permission('partner_network_create')
def create_partner():
    try:
        data = request.get_json()
        
        partner = Partner(
            name=data['name'],
            company_name=data.get('company_name'),
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            service_areas=data.get('service_areas'),
            partner_type=data['partner_type'],
            commission_rate=data.get('commission_rate', 0.0)
        )
        
        db.session.add(partner)
        db.session.commit()
        
        return jsonify(partner.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@partner_bp.route('/partners/<int:partner_id>', methods=['PUT'])
@require_permission('partner_network_update')
def update_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        data = request.get_json()
        
        partner.name = data.get('name', partner.name)
        partner.company_name = data.get('company_name', partner.company_name)
        partner.contact_person = data.get('contact_person', partner.contact_person)
        partner.email = data.get('email', partner.email)
        partner.phone = data.get('phone', partner.phone)
        partner.address = data.get('address', partner.address)
        partner.service_areas = data.get('service_areas', partner.service_areas)
        partner.partner_type = data.get('partner_type', partner.partner_type)
        partner.commission_rate = data.get('commission_rate', partner.commission_rate)
        partner.performance_rating = data.get('performance_rating', partner.performance_rating)
        partner.is_active = data.get('is_active', partner.is_active)
        partner.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(partner.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@partner_bp.route('/partners/<int:partner_id>', methods=['DELETE'])
@require_permission('partner_network_delete')
def delete_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        partner.is_active = False
        partner.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Partner deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


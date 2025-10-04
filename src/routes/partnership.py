from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.partner import Partner
from src.models.partner_performance import PartnerPerformance
from src.models.partner_contract import PartnerContract
from src.models.commission_payout import CommissionPayout
from datetime import datetime, date
import json
from src.routes.auth import require_permission, require_auth

partnership_bp = Blueprint('partnership', __name__)

# Partner Management Routes


@partnership_bp.route('/partners', methods=['GET'])
@require_permission('partner_network_read')
def get_partners():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        partner_type = request.args.get('type')
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')

        query = Partner.query

        if partner_type:
            query = query.filter(Partner.partner_type == partner_type)
        if category:
            query = query.filter(Partner.category == category)
        if status:
            query = query.filter(Partner.status == status)
        if search:
            query = query.filter(Partner.name.contains(search))

        partners = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'partners': [partner.to_dict() for partner in partners.items],
            'total': partners.total,
            'pages': partners.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners', methods=['POST'])
@require_permission('partner_network_create')
def create_partner():
    try:
        data = request.get_json()

        partner = Partner(
            name=data.get('name'),
            partner_type=data.get('partner_type'),
            category=data.get('category'),
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            website=data.get('website'),
            commission_rate=data.get('commission_rate', 0.0),
            commission_type=data.get('commission_type', 'Percentage'),
            payment_terms=data.get('payment_terms'),
            geographic_coverage=data.get('geographic_coverage'),
            notes=data.get('notes')
        )

        db.session.add(partner)
        db.session.commit()

        return jsonify(partner.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners/<int:partner_id>', methods=['GET'])
@require_permission('partner_network_read')
def get_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        return jsonify(partner.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners/<int:partner_id>', methods=['PUT'])
@require_permission('partner_network_update')
def update_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        data = request.get_json()

        for key, value in data.items():
            if hasattr(partner, key):
                setattr(partner, key, value)

        partner.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(partner.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners/<int:partner_id>', methods=['DELETE'])
@require_permission('partner_network_delete')
def delete_partner(partner_id):
    try:
        partner = Partner.query.get_or_404(partner_id)
        db.session.delete(partner)
        db.session.commit()

        return jsonify({'message': 'Partner deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Partner Performance Routes


@partnership_bp.route('/partners/<int:partner_id>/performance', methods=['GET'])
@require_permission('partner_network_read')
def get_partner_performance(partner_id):
    try:
        performance_records = PartnerPerformance.query.filter_by(partner_id=partner_id).all()
        return jsonify([record.to_dict() for record in performance_records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners/<int:partner_id>/performance', methods=['POST'])
@require_permission('partner_network_create')
def add_partner_performance(partner_id):
    try:
        data = request.get_json()

        performance = PartnerPerformance(
            partner_id=partner_id,
            metric_name=data.get('metric_name'),
            metric_value=data.get('metric_value'),
            period_start=datetime.strptime(data.get('period_start'), '%Y-%m-%d').date(),
            period_end=datetime.strptime(data.get('period_end'), '%Y-%m-%d').date()
        )

        db.session.add(performance)
        db.session.commit()

        return jsonify(performance.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Partner Contract Routes


@partnership_bp.route('/partners/<int:partner_id>/contracts', methods=['GET'])
@require_permission('partner_network_read')
def get_partner_contracts(partner_id):
    try:
        contracts = PartnerContract.query.filter_by(partner_id=partner_id).all()
        return jsonify([contract.to_dict() for contract in contracts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/partners/<int:partner_id>/contracts', methods=['POST'])
@require_permission('partner_network_create')
def add_partner_contract(partner_id):
    try:
        data = request.get_json()

        contract = PartnerContract(
            partner_id=partner_id,
            contract_title=data.get('contract_title'),
            contract_file_path=data.get('contract_file_path'),
            start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
            contract_value=data.get('contract_value'),
            commission_rate=data.get('commission_rate'),
            terms_and_conditions=data.get('terms_and_conditions')
        )

        db.session.add(contract)
        db.session.commit()

        return jsonify(contract.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Commission Management Routes


@partnership_bp.route('/partners/<int:partner_id>/commissions', methods=['GET'])
@require_permission('partner_network_read')
def get_partner_commissions(partner_id):
    try:
        commissions = CommissionPayout.query.filter_by(partner_id=partner_id).all()
        return jsonify([commission.to_dict() for commission in commissions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@partnership_bp.route('/commissions', methods=['POST'])
@require_permission('partner_network_create')
def create_commission_payout():
    try:
        data = request.get_json()

        commission = CommissionPayout(
            partner_id=data.get('partner_id'),
            order_id=data.get('order_id'),
            amount=data.get('amount'),
            commission_rate=data.get('commission_rate'),
            base_amount=data.get('base_amount'),
            payment_method=data.get('payment_method'),
            reference_number=data.get('reference_number'),
            notes=data.get('notes')
        )

        db.session.add(commission)
        db.session.commit()

        return jsonify(commission.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dashboard Analytics Routes


@partnership_bp.route('/partnership/dashboard', methods=['GET'])
@require_permission('partner_network_read')
def get_partnership_dashboard():
    try:
        # Get basic statistics
        total_partners = Partner.query.count()
        active_partners = Partner.query.filter_by(status='Active').count()
        supplier_partners = Partner.query.filter_by(partner_type='Supplier').count()
        logistics_partners = Partner.query.filter_by(partner_type='Logistics').count()

        # Get commission statistics
        total_commissions = db.session.query(db.func.sum(CommissionPayout.amount)).scalar() or 0
        pending_commissions = db.session.query(
            db.func.sum(
                CommissionPayout.amount)).filter_by(
            status='Pending').scalar() or 0

        # Get top performing partners
        top_partners = db.session.query(Partner).order_by(Partner.rating.desc()).limit(5).all()

        return jsonify({
            'total_partners': total_partners,
            'active_partners': active_partners,
            'supplier_partners': supplier_partners,
            'logistics_partners': logistics_partners,
            'total_commissions': total_commissions,
            'pending_commissions': pending_commissions,
            'top_partners': [partner.to_dict() for partner in top_partners]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Export Routes


@partnership_bp.route('/partners/export', methods=['GET'])
@require_permission('partner_network_read')
def export_partners():
    try:
        partners = Partner.query.all()

        # Create CSV-like data structure
        export_data = []
        for partner in partners:
            export_data.append({
                'ID': partner.id,
                'Name': partner.name,
                'Type': partner.partner_type,
                'Category': partner.category,
                'Contact Person': partner.contact_person,
                'Email': partner.email,
                'Phone': partner.phone,
                'Status': partner.status,
                'Commission Rate': partner.commission_rate,
                'Rating': partner.rating,
                'Total Orders': partner.total_orders,
                'Total Commission': partner.total_commission_earned,
                'Created Date': partner.created_at.strftime('%Y-%m-%d') if partner.created_at else ''
            })

        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

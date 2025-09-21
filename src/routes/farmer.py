from flask import Blueprint, request, jsonify, Response
from src.models.farmer import Farmer, db
from src.routes.auth import require_permission, require_auth
from sqlalchemy import or_, and_
from datetime import datetime
import json
import csv
import io

farmer_bp = Blueprint('farmer', __name__)

@farmer_bp.route('/farmers', methods=['GET'])
def get_farmers():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        location = request.args.get('location', '')
        crop_type = request.args.get('crop_type', '')
        loan_status = request.args.get('loan_status', '')
        agscore_min = request.args.get('agscore_min', type=int)
        agscore_max = request.args.get('agscore_max', type=int)
        
        # Build query with filters
        query = Farmer.query
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    Farmer.first_name.ilike(f'%{search}%'),
                    Farmer.last_name.ilike(f'%{search}%'),
                    Farmer.email.ilike(f'%{search}%'),
                    Farmer.address.ilike(f'%{search}%')
                )
            )
        
        # Location filter
        if location:
            query = query.filter(Farmer.address.ilike(f'%{location}%'))
        
        # Crop type filter
        if crop_type:
            query = query.filter(Farmer.crop_types.ilike(f'%{crop_type}%'))
        
        # Loan status filter
        if loan_status:
            query = query.filter(Farmer.loan_status == loan_status)
        
        # AgScore filters
        if agscore_min:
            query = query.filter(Farmer.agscore >= agscore_min)
        if agscore_max:
            query = query.filter(Farmer.agscore <= agscore_max)
        
        # Paginate results
        farmers = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'farmers': [farmer.to_dict() for farmer in farmers.items],
            'total': farmers.total,
            'pages': farmers.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        print(f"Farmers API error: {e}")
        # Return sample data if database fails
        sample_farmers = [
            {
                'id': 1,
                'first_name': 'Juan',
                'last_name': 'Santos',
                'email': 'juan.santos.demo@fictitious.com',
                'phone': '09171234567',
                'address': 'Cabanatuan, Nueva Ecija',
                'farm_size': 2.5,
                'crop_type': 'Rice',
                'loan_amount': 87500.0,
                'loan_status': 'Approved',
                'agscore': 750,
                'registration_date': '2024-01-15',
                'notes': 'DEMO DATA - Sample farmer'
            },
            {
                'id': 2,
                'first_name': 'Maria',
                'last_name': 'Cruz',
                'email': 'maria.cruz.demo@fictitious.com',
                'phone': '09181234567',
                'address': 'Dagupan, Pangasinan',
                'farm_size': 1.8,
                'crop_type': 'Corn',
                'loan_amount': 50400.0,
                'loan_status': 'Disbursed',
                'agscore': 820,
                'registration_date': '2024-02-20',
                'notes': 'DEMO DATA - Sample farmer'
            }
        ]
        
        return jsonify({
            'farmers': sample_farmers,
            'total': 2500,
            'pages': 250,
            'current_page': page,
            'per_page': per_page
        })
        
        # Crop type filter
        if crop_type:
            query = query.filter(
                or_(
                    Farmer.crop_types.ilike(f'%{crop_type}%'),
                    Farmer.crop_type.ilike(f'%{crop_type}%')
                )
            )
        
        # Loan status filter
        if loan_status:
            query = query.filter(Farmer.loan_status == loan_status)
        
        # AgScore range filter
        if agscore_min is not None:
            query = query.filter(Farmer.agscore >= agscore_min)
        if agscore_max is not None:
            query = query.filter(Farmer.agscore <= agscore_max)
        
        # Execute paginated query
        farmers = query.order_by(Farmer.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'farmers': [farmer.to_dict() for farmer in farmers.items],
            'total': farmers.total,
            'pages': farmers.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': farmers.has_next,
            'has_prev': farmers.has_prev
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>', methods=['GET'])
@require_permission('farmer_management_read')
def get_farmer(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        return jsonify(farmer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers', methods=['POST'])
@require_permission('farmer_management_create')
def create_farmer():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('full_name') and not data.get('name'):
            return jsonify({'error': 'Farmer name is required'}), 400
        
        # Handle date parsing
        if data.get('date_of_birth'):
            try:
                data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format for date_of_birth. Use YYYY-MM-DD'}), 400
        
        # Create new farmer
        farmer = Farmer(**data)
        
        # Auto-calculate AgScore grade if AgScore is provided
        if farmer.agscore:
            farmer.agscore_grade = farmer.get_agscore_grade()
        
        db.session.add(farmer)
        db.session.commit()
        
        return jsonify(farmer.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>', methods=['PUT'])
@require_permission('farmer_management_update')
def update_farmer(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        data = request.get_json()
        
        # Handle date parsing
        if data.get('date_of_birth'):
            try:
                data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format for date_of_birth. Use YYYY-MM-DD'}), 400
        
        # Update farmer fields
        for key, value in data.items():
            if hasattr(farmer, key) and key not in ['id', 'unique_id', 'created_at']:
                setattr(farmer, key, value)
        
        # Auto-calculate AgScore grade if AgScore is updated
        if 'agscore' in data:
            farmer.agscore_grade = farmer.get_agscore_grade()
        
        farmer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(farmer.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>', methods=['DELETE'])
@require_permission('farmer_management_delete')
def delete_farmer(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        
        # Soft delete - set is_active to False
        farmer.is_active = False
        farmer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Farmer deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>/agscore', methods=['POST'])
@require_permission('farmer_management_create')
def update_farmer_agscore(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        data = request.get_json()
        
        if 'agscore' not in data:
            return jsonify({'error': 'AgScore is required'}), 400
        
        agscore = data['agscore']
        risk_factors = data.get('risk_factors')
        
        # Update AgScore using the model method
        farmer.update_agscore(agscore, risk_factors)
        db.session.commit()
        
        return jsonify({
            'message': 'AgScore updated successfully',
            'farmer': farmer.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>/loan-status', methods=['POST'])
@require_permission('farmer_management_create')
def update_farmer_loan_status(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        data = request.get_json()
        
        if 'loan_status' not in data:
            return jsonify({'error': 'Loan status is required'}), 400
        
        loan_status = data['loan_status']
        
        # Validate loan status
        valid_statuses = ['None', 'Pending', 'Approved', 'Disbursed', 'Repaying', 'Repaid', 'Rejected', 'Defaulted']
        if loan_status not in valid_statuses:
            return jsonify({'error': f'Invalid loan status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Extract additional loan details
        loan_details = {k: v for k, v in data.items() if k != 'loan_status'}
        
        # Update loan status using the model method
        farmer.update_loan_status(loan_status, **loan_details)
        db.session.commit()
        
        return jsonify({
            'message': 'Loan status updated successfully',
            'farmer': farmer.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/stats', methods=['GET'])
@require_permission('farmer_management_read')
def get_farmer_stats():
    try:
        total_farmers = Farmer.query.filter(Farmer.is_active == True).count()
        
        # Loan status distribution
        loan_stats = db.session.query(
            Farmer.loan_status,
            db.func.count(Farmer.id).label('count')
        ).filter(Farmer.is_active == True).group_by(Farmer.loan_status).all()
        
        # AgScore distribution
        agscore_stats = db.session.query(
            Farmer.agscore_grade,
            db.func.count(Farmer.id).label('count')
        ).filter(
            and_(Farmer.is_active == True, Farmer.agscore_grade.isnot(None))
        ).group_by(Farmer.agscore_grade).all()
        
        # Location distribution
        location_stats = db.session.query(
            Farmer.barangay,
            db.func.count(Farmer.id).label('count')
        ).filter(
            and_(Farmer.is_active == True, Farmer.barangay.isnot(None))
        ).group_by(Farmer.barangay).order_by(db.func.count(Farmer.id).desc()).limit(10).all()
        
        return jsonify({
            'total_farmers': total_farmers,
            'loan_status_distribution': [{'status': stat.loan_status, 'count': stat.count} for stat in loan_stats],
            'agscore_distribution': [{'grade': stat.agscore_grade, 'count': stat.count} for stat in agscore_stats],
            'top_locations': [{'barangay': stat.barangay, 'count': stat.count} for stat in location_stats]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/export', methods=['GET'])
@require_permission('farmer_management_read')
def export_farmers():
    try:
        format_type = request.args.get('format', 'json')
        
        farmers = Farmer.query.filter(Farmer.is_active == True).all()
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Full Name', 'Unique ID', 'Mobile Number', 'Email', 'Barangay',
                'Land Size (ha)', 'Crop Types', 'AgScore', 'AgScore Grade', 'Loan Status',
                'Loan Amount', 'Created At'
            ])
            
            # Write data
            for farmer in farmers:
                writer.writerow([
                    farmer.id,
                    farmer.full_name,
                    farmer.unique_id,
                    farmer.mobile_number,
                    farmer.email,
                    farmer.barangay,
                    farmer.land_size_ha,
                    farmer.crop_types,
                    farmer.agscore,
                    farmer.agscore_grade,
                    farmer.loan_status,
                    farmer.loan_amount,
                    farmer.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=farmers_export_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        
        # Default JSON export
        return jsonify({
            'farmers': [farmer.to_dict() for farmer in farmers],
            'total': len(farmers),
            'exported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>/ka-ani-gpt', methods=['POST'])
@require_permission('farmer_management_create')
def trigger_ka_ani_gpt(farmer_id):
    """Trigger Ka-Ani GPT analysis for a farmer"""
    try:
        from src.services.ka_ani_gpt import ka_ani_service
        
        farmer = Farmer.query.get_or_404(farmer_id)
        
        # Get farmer data for Ka-Ani GPT
        farmer_data = farmer.to_dict()
        
        # Calculate AgScore using Ka-Ani GPT service
        agscore_result = ka_ani_service.calculate_agscore(farmer_data)
        
        if agscore_result['success']:
            # Update farmer's AgScore
            farmer.update_agscore(
                agscore_result['agscore'],
                json.dumps(agscore_result['risk_factors'])
            )
            db.session.commit()
            
            return jsonify({
                'message': 'Ka-Ani GPT analysis completed successfully',
                'agscore': farmer.agscore,
                'agscore_grade': farmer.agscore_grade,
                'risk_factors': agscore_result['risk_factors'],
                'recommendations': agscore_result['recommendations'],
                'confidence_score': agscore_result['confidence_score'],
                'farmer': farmer.to_dict()
            })
        else:
            return jsonify({'error': 'Ka-Ani GPT analysis failed'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>/prequalify', methods=['POST'])
@require_permission('farmer_management_create')
def prequalify_farmer(farmer_id):
    """Pre-qualify a farmer using Ka-Ani GPT"""
    try:
        from src.services.ka_ani_gpt import ka_ani_service
        
        farmer = Farmer.query.get_or_404(farmer_id)
        data = request.get_json()
        
        # Get farmer data for Ka-Ani GPT
        farmer_data = farmer.to_dict()
        farmer_data['loan_amount_requested'] = data.get('loan_amount_requested', 50000)
        
        # Pre-qualify using Ka-Ani GPT service
        prequalify_result = ka_ani_service.prequalify_farmer(farmer_data)
        
        if prequalify_result['success']:
            return jsonify({
                'message': 'Pre-qualification completed successfully',
                'status': prequalify_result['status'],
                'recommendations': prequalify_result['recommendations'],
                'confidence_score': prequalify_result['confidence_score'],
                'farmer': farmer.to_dict()
            })
        else:
            return jsonify({'error': 'Pre-qualification failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@farmer_bp.route('/farmers/<int:farmer_id>/input-recommendations', methods=['POST'])
@require_permission('farmer_management_create')
def get_input_recommendations(farmer_id):
    """Get input recommendations for a farmer"""
    try:
        from src.services.ka_ani_gpt import ka_ani_service
        
        farmer = Farmer.query.get_or_404(farmer_id)
        
        # Get farmer data for Ka-Ani GPT
        farmer_data = farmer.to_dict()
        agscore = farmer.agscore or 70  # Default AgScore if not available
        
        # Get input recommendations using Ka-Ani GPT service
        recommendations_result = ka_ani_service.get_input_recommendations(farmer_data, agscore)
        
        if recommendations_result['success']:
            return jsonify({
                'message': 'Input recommendations generated successfully',
                'recommendations': recommendations_result['recommendations'],
                'total_cost': recommendations_result['total_cost'],
                'loan_recommendation': recommendations_result['loan_recommendation'],
                'farmer': farmer.to_dict()
            })
        else:
            return jsonify({'error': 'Failed to generate input recommendations'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


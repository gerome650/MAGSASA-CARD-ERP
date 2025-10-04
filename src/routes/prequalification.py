"""
Pre-qualification API for KaAni Agricultural Assessment
Provides loan pre-qualification functionality for field officers and managers
"""

from flask import Blueprint, request, jsonify, session
import json
import logging
from datetime import datetime
from src.kaani_functions import execute_kaani_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

prequalification_bp = Blueprint('prequalification', __name__, url_prefix='/api/prequalification')


@prequalification_bp.route('/assess', methods=['POST'])
def assess_farmer():
    """Assess farmer for loan pre-qualification using KaAni"""
    try:
        data = request.get_json()

        # Required fields
        required_fields = ['farmer_name', 'location', 'crop', 'land_size_ha', 'loan_amount_requested']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'required_fields': required_fields
            }), 400

        # Get user info for audit trail
        user_id = session.get('user_id', 'anonymous')
        user_name = session.get('user_name', 'Unknown')
        user_role = session.get('user', {}).get('role', 'officer')

        # Execute pre-qualification assessment
        assessment_result = execute_kaani_function(
            'prequalify_farmer',
            farmer_name=data['farmer_name'],
            location=data['location'],
            crop=data['crop'],
            land_size_ha=data['land_size_ha'],
            loan_amount_requested=data['loan_amount_requested']
        )

        if 'error' in assessment_result:
            return jsonify({
                'error': 'Assessment failed',
                'details': assessment_result['error']
            }), 500

        # Add audit information
        assessment_result.update({
            'assessed_by': user_name,
            'assessor_id': user_id,
            'assessor_role': user_role,
            'assessment_timestamp': datetime.now().isoformat()
        })

        # Log the assessment
        logger.info(
            f"Pre-qualification assessment - Officer: {user_name}, Farmer: {data['farmer_name']}, Status: {assessment_result.get('status')}")

        return jsonify({
            'success': True,
            'assessment': assessment_result
        })

    except Exception as e:
        logger.error(f"Error in farmer assessment: {e}")
        return jsonify({
            'error': 'Internal server error during assessment',
            'details': str(e)
        }), 500


@prequalification_bp.route('/batch-assess', methods=['POST'])
def batch_assess_farmers():
    """Batch assess multiple farmers for pre-qualification"""
    try:
        data = request.get_json()
        farmers = data.get('farmers', [])

        if not farmers:
            return jsonify({'error': 'No farmers provided for assessment'}), 400

        if len(farmers) > 50:
            return jsonify({'error': 'Maximum 50 farmers allowed per batch'}), 400

        # Get user info
        user_id = session.get('user_id', 'anonymous')
        user_name = session.get('user_name', 'Unknown')
        user_role = session.get('user', {}).get('role', 'officer')

        results = []

        for i, farmer_data in enumerate(farmers):
            try:
                # Validate required fields
                required_fields = ['farmer_name', 'location', 'crop', 'land_size_ha', 'loan_amount_requested']
                missing_fields = [field for field in required_fields if not farmer_data.get(field)]

                if missing_fields:
                    results.append({
                        'farmer_index': i,
                        'farmer_name': farmer_data.get('farmer_name', 'Unknown'),
                        'error': f'Missing fields: {", ".join(missing_fields)}',
                        'status': 'Error'
                    })
                    continue

                # Execute assessment
                assessment_result = execute_kaani_function(
                    'prequalify_farmer',
                    farmer_name=farmer_data['farmer_name'],
                    location=farmer_data['location'],
                    crop=farmer_data['crop'],
                    land_size_ha=farmer_data['land_size_ha'],
                    loan_amount_requested=farmer_data['loan_amount_requested']
                )

                if 'error' in assessment_result:
                    results.append({
                        'farmer_index': i,
                        'farmer_name': farmer_data['farmer_name'],
                        'error': assessment_result['error'],
                        'status': 'Error'
                    })
                else:
                    # Add audit info
                    assessment_result.update({
                        'farmer_index': i,
                        'assessed_by': user_name,
                        'assessor_id': user_id,
                        'assessor_role': user_role,
                        'assessment_timestamp': datetime.now().isoformat()
                    })
                    results.append(assessment_result)

            except Exception as e:
                results.append({
                    'farmer_index': i,
                    'farmer_name': farmer_data.get('farmer_name', 'Unknown'),
                    'error': str(e),
                    'status': 'Error'
                })

        # Summary statistics
        total_farmers = len(results)
        pre_qualified = len([r for r in results if r.get('status') == 'Pre-qualified'])
        needs_info = len([r for r in results if r.get('status') == 'Needs More Info'])
        not_qualified = len([r for r in results if r.get('status') == 'Not Qualified'])
        errors = len([r for r in results if r.get('status') == 'Error'])

        summary = {
            'total_farmers': total_farmers,
            'pre_qualified': pre_qualified,
            'needs_more_info': needs_info,
            'not_qualified': not_qualified,
            'errors': errors,
            'success_rate': round((total_farmers - errors) / total_farmers * 100, 1) if total_farmers > 0 else 0
        }

        logger.info(
            f"Batch assessment - Officer: {user_name}, Farmers: {total_farmers}, Pre-qualified: {pre_qualified}")

        return jsonify({
            'success': True,
            'summary': summary,
            'results': results,
            'batch_timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in batch assessment: {e}")
        return jsonify({
            'error': 'Internal server error during batch assessment',
            'details': str(e)
        }), 500


@prequalification_bp.route('/templates', methods=['GET'])
def get_assessment_templates():
    """Get pre-qualification assessment templates and examples"""
    try:
        templates = {
            'single_farmer': {
                'farmer_name': 'Juan Dela Cruz',
                'location': 'Laguna',
                'crop': 'rice',
                'land_size_ha': 2.5,
                'loan_amount_requested': 75000
            },
            'batch_farmers': {
                'farmers': [
                    {
                        'farmer_name': 'Maria Santos',
                        'location': 'Nueva Ecija',
                        'crop': 'rice',
                        'land_size_ha': 3.0,
                        'loan_amount_requested': 90000
                    },
                    {
                        'farmer_name': 'Pedro Reyes',
                        'location': 'Pangasinan',
                        'crop': 'corn',
                        'land_size_ha': 1.5,
                        'loan_amount_requested': 45000
                    }
                ]
            },
            'field_definitions': {
                'farmer_name': 'Full name of the farmer',
                'location': 'Municipality or province where the farm is located',
                'crop': 'Primary crop type (rice, corn, vegetables, etc.)',
                'land_size_ha': 'Farm size in hectares (decimal allowed)',
                'loan_amount_requested': 'Requested loan amount in PHP'
            },
            'crop_types': ['rice', 'corn', 'vegetables', 'sugarcane', 'coconut', 'banana'],
            'assessment_criteria': {
                'land_size': 'Larger farms generally score higher (minimum 0.5 ha recommended)',
                'crop_type': 'Rice and corn have established markets and support systems',
                'loan_amount': 'Should not exceed 70% of expected annual farm income',
                'location': 'Areas with good agricultural infrastructure score higher'
            }
        }

        return jsonify({
            'success': True,
            'templates': templates
        })

    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({
            'error': 'Failed to get templates',
            'details': str(e)
        }), 500


@prequalification_bp.route('/status', methods=['GET'])
def prequalification_status():
    """Get pre-qualification service status"""
    try:
        user_role = session.get('user', {}).get('role', 'farmer')

        # Check if user has access to pre-qualification features
        authorized_roles = ['officer', 'manager', 'admin', 'superadmin']
        has_access = user_role in authorized_roles

        return jsonify({
            'status': 'active',
            'user_role': user_role,
            'has_access': has_access,
            'features': {
                'single_assessment': has_access,
                'batch_assessment': has_access and user_role in ['manager', 'admin', 'superadmin'],
                'templates': has_access,
                'audit_trail': True
            },
            'limits': {
                'max_batch_size': 50,
                'assessment_timeout': 30
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

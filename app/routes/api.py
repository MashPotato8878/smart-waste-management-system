from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..models import Bin
from .. import db
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/bins', methods=['POST'])
@login_required
def create_bin():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    
    # Validate required fields
    required_fields = ['location', 'status', 'latitude', 'longitude']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        # Convert coordinates to float
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])

        # Validate coordinate ranges
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({'success': False, 'message': 'Invalid coordinates'}), 400

        # Create new bin
        new_bin = Bin(
            location=data['location'],
            status=data['status'],
            latitude=latitude,
            longitude=longitude,
            last_updated=datetime.utcnow()
        )

        db.session.add(new_bin)
        db.session.commit()

        return jsonify({
            'success': True,
            'bin': {
                'id': new_bin.id,
                'location': new_bin.location,
                'status': new_bin.status,
                'latitude': new_bin.latitude,
                'longitude': new_bin.longitude,
                'last_updated': new_bin.last_updated.isoformat()
            }
        })

    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid coordinate values'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/api/bins/<int:bin_id>', methods=['GET'])
@login_required
def get_bin(bin_id):
    bin = Bin.query.get_or_404(bin_id)
    return jsonify({
        'id': bin.id,
        'location': bin.location,
        'status': bin.status,
        'latitude': bin.latitude,
        'longitude': bin.longitude,
        'last_updated': bin.last_updated.isoformat()
    })

@api_bp.route('/api/bins/<int:bin_id>', methods=['PUT'])
@login_required
def update_bin(bin_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    bin = Bin.query.get_or_404(bin_id)
    data = request.get_json()

    bin.location = data.get('location', bin.location)
    bin.status = data.get('status', bin.status)
    bin.latitude = float(data.get('latitude', bin.latitude))
    bin.longitude = float(data.get('longitude', bin.longitude))

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/api/bins/<int:bin_id>', methods=['DELETE'])
@login_required
def delete_bin(bin_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    bin = Bin.query.get_or_404(bin_id)
    try:
        db.session.delete(bin)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 
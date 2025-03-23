from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..models import Bin
from .. import db

api_bp = Blueprint('api', __name__)

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
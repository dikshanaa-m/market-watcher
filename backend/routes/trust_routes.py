from flask import Blueprint, jsonify
from services.data_trust_service import DataTrustService

trust_bp = Blueprint('trust', __name__)

@trust_bp.route('/api/data-trust/status', methods=['GET'])
def get_trust_status():
    try:
        summary = DataTrustService.get_watchlist_trust_summary(watchlist_id=1)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get data trust status: {str(e)}"
        }), 500

@trust_bp.route('/api/data-trust/conflicts', methods=['GET'])
def get_trust_conflicts():
    try:
        summary = DataTrustService.get_watchlist_trust_summary(watchlist_id=1)
        return jsonify({
            "status": "success",
            "conflict_count": summary["conflict_count"],
            "conflicts": summary["active_conflicts"]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to query data conflicts: {str(e)}"
        }), 500

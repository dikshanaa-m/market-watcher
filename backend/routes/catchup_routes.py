from flask import Blueprint, jsonify
from services.catchup_service import CatchUpService

catchup_bp = Blueprint('catchup', __name__)

@catchup_bp.route('/api/catchup/digest', methods=['GET'])
def get_catchup_digest():
    try:
        digest = CatchUpService.get_digest_for_user(user_id=1, watchlist_id=1)
        return jsonify(digest), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate catch-up digest: {str(e)}"
        }), 500

@catchup_bp.route('/api/catchup/mark-seen', methods=['POST'])
def mark_watchlist_seen():
    try:
        res = CatchUpService.update_last_seen(user_id=1, watchlist_id=1)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to update last-seen timestamp: {str(e)}"
        }), 500

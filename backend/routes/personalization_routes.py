from flask import Blueprint, jsonify, request
from services.personalization_service import PersonalizationService

personalization_bp = Blueprint('personalization', __name__)

@personalization_bp.route('/api/interactions', methods=['POST'])
def log_interaction():
    data = request.get_json(silent=True) or {}
    interaction_type = data.get('interaction_type', 'news_clicked')
    ticker = data.get('ticker', 'NVDA')
    event_type = data.get('event_type')
    user_id = data.get('user_id', 1)

    try:
        res = PersonalizationService.record_interaction(
            user_id=user_id,
            ticker=ticker,
            interaction_type=interaction_type,
            event_type=event_type
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to record interaction: {str(e)}"
        }), 500

@personalization_bp.route('/api/personalization/weights', methods=['GET'])
def get_weights():
    user_id = request.args.get('user_id', default=1, type=int)
    try:
        pref = PersonalizationService.get_user_weights(user_id=user_id)
        is_default = (pref.volatility_weight == 0.40 and pref.volume_weight == 0.30 and pref.news_weight == 0.20 and pref.extreme_weight == 0.10)
        return jsonify({
            "status": "success",
            "is_default": is_default,
            "weights": pref.to_dict(),
            "explanation": "Default weights (40% Volatility, 30% Volume, 20% News, 10% Extreme)" if is_default else "Personalized weights updated based on your interaction feedback."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get user weights: {str(e)}"
        }), 500

@personalization_bp.route('/api/personalization/reset-weights', methods=['POST'])
def reset_weights():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id', 1)
    try:
        res = PersonalizationService.reset_user_weights(user_id=user_id)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to reset user weights: {str(e)}"
        }), 500

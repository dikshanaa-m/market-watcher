from flask import Blueprint, jsonify, request
from services.ai_explanation_service import AIExplanationService

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/api/ai/explain/<ticker>', methods=['GET'])
def get_explanation(ticker):
    try:
        res = AIExplanationService.generate_explanation(ticker)
        if res.get("status") == "error":
            return jsonify(res), 404
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate AI explanation: {str(e)}"
        }), 500

@ai_bp.route('/api/ai/explain-digest', methods=['POST'])
def explain_digest():
    try:
        data = request.get_json(silent=True) or {}
        tickers = data.get("tickers", [])
        
        explanations = {}
        for ticker in tickers:
            explanations[ticker] = AIExplanationService.generate_explanation(ticker)

        return jsonify({
            "status": "success",
            "explanations": explanations
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate digest explanations: {str(e)}"
        }), 500

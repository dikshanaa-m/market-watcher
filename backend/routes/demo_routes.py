from flask import Blueprint, jsonify
from services.mock_data_service import MockDataService

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/api/demo/reset', methods=['GET', 'POST'])
def reset_demo():
    try:
        result = MockDataService.seed_initial_data()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to reset demo database: {str(e)}"
        }), 500

@demo_bp.route('/api/demo/run', methods=['POST'])
def run_demo():
    try:
        result = MockDataService.run_demo_scenario()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to run demo scenario: {str(e)}"
        }), 500

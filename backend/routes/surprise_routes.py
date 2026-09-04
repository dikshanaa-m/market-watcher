from flask import Blueprint, jsonify
from services.surprise_service import SurpriseScoringService
from models.surprise import ComputedSurpriseScore
from models.watchlist import WatchlistStock

surprise_bp = Blueprint('surprise', __name__)

@surprise_bp.route('/api/surprise-scores', methods=['GET'])
def get_all_surprise_scores():
    active_stocks = WatchlistStock.query.filter_by(is_active=True).all()
    results = []
    
    for stock in active_stocks:
        # Get latest computed score for stock
        score = ComputedSurpriseScore.query.filter_by(ticker=stock.ticker)\
            .order_by(ComputedSurpriseScore.calculated_at.desc()).first()
            
        if not score:
            # Calculate dynamically on-demand if not yet computed
            score_dict = SurpriseScoringService.calculate_for_ticker(stock.ticker)
        else:
            score_dict = score.to_dict()
            
        if score_dict:
            results.append(score_dict)

    # Sort ranked by highest surprise score first
    results.sort(key=lambda x: x["surprise_score"], reverse=True)

    return jsonify({
        "status": "success",
        "count": len(results),
        "data": results
    }), 200

@surprise_bp.route('/api/surprise-scores/<ticker>', methods=['GET'])
def get_ticker_surprise_score(ticker):
    score = ComputedSurpriseScore.query.filter_by(ticker=ticker.upper())\
        .order_by(ComputedSurpriseScore.calculated_at.desc()).first()
        
    if not score:
        score_dict = SurpriseScoringService.calculate_for_ticker(ticker)
        if not score_dict:
            return jsonify({"status": "error", "message": f"No score available for ticker {ticker}"}), 404
        return jsonify({"status": "success", "data": score_dict}), 200

    return jsonify({
        "status": "success",
        "data": score.to_dict()
    }), 200

@surprise_bp.route('/api/surprise-scores/recalculate', methods=['POST'])
def recalculate_surprise_scores():
    try:
        res = SurpriseScoringService.recalculate_all()
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to recalculate surprise scores: {str(e)}"
        }), 500

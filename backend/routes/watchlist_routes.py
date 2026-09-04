from flask import Blueprint, jsonify, request
from models.watchlist import Watchlist, WatchlistStock
from models.market import MarketEvent

watchlist_bp = Blueprint('watchlist', __name__)

@watchlist_bp.route('/api/watchlists', methods=['GET'])
def get_watchlists():
    watchlists = Watchlist.query.all()
    return jsonify({
        "status": "success",
        "data": [w.to_dict() for w in watchlists]
    }), 200

@watchlist_bp.route('/api/watchlists/<int:watchlist_id>/stocks', methods=['GET'])
def get_watchlist_stocks(watchlist_id):
    watchlist = Watchlist.query.get(watchlist_id)
    if not watchlist:
        return jsonify({"status": "error", "message": "Watchlist not found"}), 404
        
    stocks = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, is_active=True).all()
    result = []
    
    for s in stocks:
        stock_dict = s.to_dict()
        # Attach latest market event for baseline overview display
        latest_event = MarketEvent.query.filter_by(ticker=s.ticker)\
            .order_by(MarketEvent.timestamp.desc()).first()
        stock_dict['latest_event'] = latest_event.to_dict() if latest_event else None
        result.append(stock_dict)
        
    return jsonify({
        "status": "success",
        "watchlist_id": watchlist_id,
        "watchlist_name": watchlist.name,
        "stocks": result
    }), 200

from flask import Blueprint, jsonify, request
from models.market import MarketEvent, NewsEvent, DataSource

market_bp = Blueprint('market', __name__)

@market_bp.route('/api/market-events', methods=['GET'])
def get_market_events():
    ticker = request.args.get('ticker')
    limit = request.args.get('limit', default=100, type=int)
    
    query = MarketEvent.query
    if ticker:
        query = query.filter_by(ticker=ticker.upper())
        
    events = query.order_by(MarketEvent.timestamp.desc()).limit(limit).all()
    return jsonify({
        "status": "success",
        "count": len(events),
        "data": [e.to_dict() for e in events]
    }), 200

@market_bp.route('/api/news', methods=['GET'])
def get_news_events():
    ticker = request.args.get('ticker')
    limit = request.args.get('limit', default=50, type=int)
    
    query = NewsEvent.query
    if ticker:
        query = query.filter_by(ticker=ticker.upper())
        
    news = query.order_by(NewsEvent.published_at.desc()).limit(limit).all()
    return jsonify({
        "status": "success",
        "count": len(news),
        "data": [n.to_dict() for n in news]
    }), 200

@market_bp.route('/api/data-sources', methods=['GET'])
def get_data_sources():
    sources = DataSource.query.all()
    return jsonify({
        "status": "success",
        "data": [ds.to_dict() for ds in sources]
    }), 200

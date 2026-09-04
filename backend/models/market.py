import json
from datetime import datetime
from database import db

class MarketEvent(db.Model):
    __tablename__ = 'market_events'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False) # e.g. price_update, volume_update, market_event
    price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=True)
    price_change_percent = db.Column(db.Float, nullable=True)
    volume = db.Column(db.BigInteger, nullable=False)
    average_volume = db.Column(db.BigInteger, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = db.Column(db.String(50), nullable=False, default='PrimaryFeed')
    source_timestamp = db.Column(db.DateTime, nullable=True)
    freshness_status = db.Column(db.String(50), nullable=False, default='live') # e.g. live, delayed, stale, conflicting
    metadata_json = db.Column(db.Text, nullable=True) # JSON text for custom metadata (e.g. sector movement, secondary source prices)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_metadata(self):
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except Exception:
                return {}
        return {}

    def set_metadata(self, data):
        self.metadata_json = json.dumps(data) if data else None

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'event_type': self.event_type,
            'price': self.price,
            'previous_price': self.previous_price,
            'price_change_percent': round(self.price_change_percent, 2) if self.price_change_percent is not None else None,
            'volume': self.volume,
            'average_volume': self.average_volume,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'source_timestamp': self.source_timestamp.isoformat() if self.source_timestamp else None,
            'freshness_status': self.freshness_status,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NewsEvent(db.Model):
    __tablename__ = 'news_events'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    headline = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    sentiment = db.Column(db.String(20), nullable=False, default='neutral') # e.g. positive, negative, neutral
    event_type = db.Column(db.String(50), nullable=False, default='earnings_guidance')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'headline': self.headline,
            'summary': self.summary,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'sentiment': self.sentiment,
            'event_type': self.event_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    source_type = db.Column(db.String(50), nullable=False) # e.g. real_time_exchange, delayed_feed, news_wire
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

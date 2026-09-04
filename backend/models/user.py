from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, default='demo_user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserLastSeen(db.Model):
    __tablename__ = 'user_last_seen'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    last_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'watchlist_id': self.watchlist_id,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False) # e.g. alert_opened, alert_dismissed, news_clicked, volume_ignored
    event_type = db.Column(db.String(50), nullable=True) # e.g. volume_spike, price_drop, quiet_sector
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ticker': self.ticker,
            'interaction_type': self.interaction_type,
            'event_type': self.event_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserPreferenceWeights(db.Model):
    __tablename__ = 'user_preference_weights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    volatility_weight = db.Column(db.Float, nullable=False, default=0.40)
    volume_weight = db.Column(db.Float, nullable=False, default=0.30)
    news_weight = db.Column(db.Float, nullable=False, default=0.20)
    extreme_weight = db.Column(db.Float, nullable=False, default=0.10)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'volatility_weight': round(self.volatility_weight, 3),
            'volume_weight': round(self.volume_weight, 3),
            'news_weight': round(self.news_weight, 3),
            'extreme_weight': round(self.extreme_weight, 3),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

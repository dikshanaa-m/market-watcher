from datetime import datetime
from database import db

class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='Primary Watchlist')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stocks = db.relationship('WatchlistStock', backref='watchlist', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'stocks': [s.to_dict() for s in self.stocks if s.is_active]
        }

class WatchlistStock(db.Model):
    __tablename__ = 'watchlist_stocks'
    __table_args__ = (
        db.UniqueConstraint('watchlist_id', 'ticker', name='unique_active_watchlist_ticker'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'watchlist_id': self.watchlist_id,
            'ticker': self.ticker,
            'company_name': self.company_name,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'is_active': self.is_active
        }

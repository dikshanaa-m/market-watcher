import json
from datetime import datetime
from database import db

class ComputedSurpriseScore(db.Model):
    __tablename__ = 'computed_surprise_scores'

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    market_event_id = db.Column(db.Integer, db.ForeignKey('market_events.id'), nullable=False)
    surprise_score = db.Column(db.Integer, nullable=False) # 0 to 100
    category = db.Column(db.String(30), nullable=False) # VERY UNUSUAL, UNUSUAL, MODERATE, NORMAL
    
    # Component Scores (0 to 100)
    volatility_score = db.Column(db.Float, nullable=False)
    volume_score = db.Column(db.Float, nullable=False)
    news_score = db.Column(db.Float, nullable=False)
    extreme_score = db.Column(db.Float, nullable=False)
    
    # Underlying Calculated Metrics
    volatility_z_score = db.Column(db.Float, nullable=False)
    volume_ratio = db.Column(db.Float, nullable=False)
    historical_std_dev = db.Column(db.Float, nullable=False)
    historical_extreme_percentile = db.Column(db.Float, nullable=False)
    
    explanation_factors_json = db.Column(db.Text, nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_explanation_factors(self):
        if self.explanation_factors_json:
            try:
                return json.loads(self.explanation_factors_json)
            except Exception:
                return []
        return []

    def set_explanation_factors(self, factors):
        self.explanation_factors_json = json.dumps(factors) if factors else '[]'

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'market_event_id': self.market_event_id,
            'surprise_score': self.surprise_score,
            'category': self.category,
            'volatility_score': round(self.volatility_score, 1),
            'volume_score': round(self.volume_score, 1),
            'news_score': round(self.news_score, 1),
            'extreme_score': round(self.extreme_score, 1),
            'volatility_z_score': round(self.volatility_z_score, 2),
            'volume_ratio': round(self.volume_ratio, 2),
            'historical_std_dev': round(self.historical_std_dev, 2),
            'historical_extreme_percentile': round(self.historical_extreme_percentile, 1),
            'explanation_factors': self.get_explanation_factors(),
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }

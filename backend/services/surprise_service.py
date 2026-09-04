import math
import json
from datetime import datetime, timedelta
from database import db
from models.market import MarketEvent, NewsEvent
from models.surprise import ComputedSurpriseScore
from models.watchlist import WatchlistStock
from models.user import UserPreferenceWeights

class SurpriseScoringService:
    
    @staticmethod
    def calculate_for_ticker(ticker, user_id=1):
        ticker = ticker.upper()

        # Fetch personalized user factor weights (default 0.40, 0.30, 0.20, 0.10)
        pref = UserPreferenceWeights.query.filter_by(user_id=user_id).first()
        w_vol = pref.volatility_weight if pref else 0.40
        w_v = pref.volume_weight if pref else 0.30
        w_news = pref.news_weight if pref else 0.20
        w_ext = pref.extreme_weight if pref else 0.10
        
        # 1. Fetch latest MarketEvent
        latest_event = MarketEvent.query.filter_by(ticker=ticker)\
            .order_by(MarketEvent.timestamp.desc()).first()
            
        if not latest_event:
            return None

        # 2. Fetch prior MarketEvents excluding the current event (up to 60 prior observations)
        prior_events = MarketEvent.query.filter(
            MarketEvent.ticker == ticker,
            MarketEvent.id != latest_event.id
        ).order_by(MarketEvent.timestamp.desc()).limit(60).all()

        current_change = abs(latest_event.price_change_percent or 0.0)
        current_volume = latest_event.volume or 0

        # --- FACTOR 1: Price Volatility Abnormality ---
        if prior_events and len(prior_events) >= 2:
            historical_changes = [e.price_change_percent or 0.0 for e in prior_events]
            mean_change = sum(historical_changes) / len(historical_changes)
            variance = sum((x - mean_change) ** 2 for x in historical_changes) / len(historical_changes)
            sigma60 = math.sqrt(variance)
        else:
            sigma60 = 0.0

        if sigma60 > 0:
            z_price = current_change / sigma60
            s_volatility = min(100.0, z_price * 25.0)
        else:
            z_price = 0.0
            s_volatility = 0.0

        # --- FACTOR 2: Volume Spike ---
        if prior_events:
            avg_volume60 = sum(e.volume for e in prior_events) / len(prior_events)
        else:
            avg_volume60 = latest_event.average_volume or current_volume or 1

        if avg_volume60 > 0:
            volume_ratio = current_volume / avg_volume60
            s_volume = min(100.0, max(0.0, (volume_ratio - 1.0) * 40.0))
        else:
            volume_ratio = 1.0
            s_volume = 0.0

        # --- FACTOR 3: News Impact ---
        cutoff_time = latest_event.timestamp - timedelta(hours=48)
        recent_news = NewsEvent.query.filter(
            NewsEvent.ticker == ticker,
            NewsEvent.published_at >= cutoff_time
        ).order_by(NewsEvent.published_at.desc()).all()

        negative_news = [n for n in recent_news if n.sentiment == 'negative']
        positive_news = [n for n in recent_news if n.sentiment == 'positive']

        if negative_news:
            s_news = 100.0
            primary_news = negative_news[0]
            news_explanation = f"Negative news detected: \"{primary_news.headline}\""
        elif positive_news:
            s_news = 50.0
            primary_news = positive_news[0]
            news_explanation = f"Positive news detected: \"{primary_news.headline}\""
        else:
            s_news = 0.0
            primary_news = None
            news_explanation = "No major market news detected"

        # --- FACTOR 4: Historical Extreme Percentile ---
        if prior_events:
            historical_abs_moves = [abs(e.price_change_percent or 0.0) for e in prior_events]
            smaller_or_equal_count = sum(1 for move in historical_abs_moves if move <= current_change)
            extreme_percentile = (smaller_or_equal_count / len(historical_abs_moves)) * 100.0
        else:
            extreme_percentile = 50.0

        s_extreme = min(100.0, max(0.0, round(extreme_percentile)))

        # --- FINAL SCORE CALCULATION (USING PERSONALIZED WEIGHTS) ---
        raw_final_score = (
            w_vol * s_volatility +
            w_v * s_volume +
            w_news * s_news +
            w_ext * s_extreme
        )
        final_score = int(round(min(100.0, max(0.0, raw_final_score))))

        # --- CATEGORY CLASSIFICATION ---
        if final_score >= 80:
            category = "VERY UNUSUAL"
        elif final_score >= 50:
            category = "UNUSUAL"
        elif final_score >= 25:
            category = "MODERATE"
        else:
            category = "NORMAL"

        # --- DYNAMIC AUDIT EXPLANATIONS ---
        explanations = []
        
        # Personalized Weight Bullet (if modified from default 40/30/20/10)
        is_personalized = (w_vol != 0.40 or w_v != 0.30 or w_news != 0.20 or w_ext != 0.10)
        if is_personalized:
            explanations.append(f"Personalized Score: Adjusted for your feedback (Volatility {int(w_vol*100)}%, Volume {int(w_v*100)}%, News {int(w_news*100)}%, Extreme {int(w_ext*100)}%)")

        # 1. Price Volatility Bullet
        if sigma60 > 0:
            explanations.append(f"{latest_event.price_change_percent:+.1f}% price move is {z_price:.1f}× its normal daily volatility of {sigma60:.1f}%")
        else:
            explanations.append(f"{latest_event.price_change_percent:+.1f}% price move (historical volatility baseline limited)")

        # 2. Volume Spike Bullet
        if volume_ratio >= 1.2:
            explanations.append(f"Trading volume is {volume_ratio:.1f}× the 60-day average")
        else:
            explanations.append(f"Trading volume is normal ({volume_ratio:.1f}× 60-day average)")

        # 3. Extreme Percentile Bullet
        if extreme_percentile >= 90:
            explanations.append("Today's move is near the largest historical moves")
        elif extreme_percentile >= 60:
            explanations.append(f"Move is in the upper {100 - extreme_percentile:.0f}% of historical moves")
        else:
            explanations.append("Move is within normal historical distribution range")

        # 4. News Bullet
        if primary_news:
            explanations.append(news_explanation)

        # --- PERSIST OR UPDATE IN DB ---
        existing_score = ComputedSurpriseScore.query.filter_by(
            ticker=ticker,
            market_event_id=latest_event.id
        ).first()

        if not existing_score:
            existing_score = ComputedSurpriseScore(
                ticker=ticker,
                market_event_id=latest_event.id
            )
            db.session.add(existing_score)

        existing_score.surprise_score = final_score
        existing_score.category = category
        existing_score.volatility_score = s_volatility
        existing_score.volume_score = s_volume
        existing_score.news_score = s_news
        existing_score.extreme_score = s_extreme
        existing_score.volatility_z_score = z_price
        existing_score.volume_ratio = volume_ratio
        existing_score.historical_std_dev = sigma60
        existing_score.historical_extreme_percentile = extreme_percentile
        existing_score.set_explanation_factors(explanations)
        existing_score.calculated_at = datetime.utcnow()

        db.session.commit()
        return existing_score.to_dict()

    @staticmethod
    def recalculate_all(user_id=1):
        """Recalculates Surprise Scores for all active watchlist stocks using user's personalized weights."""
        active_stocks = WatchlistStock.query.filter_by(is_active=True).all()
        results = []
        errors = []

        for stock in active_stocks:
            try:
                score_dict = SurpriseScoringService.calculate_for_ticker(stock.ticker, user_id=user_id)
                if score_dict:
                    results.append(score_dict)
            except Exception as e:
                errors.append({"ticker": stock.ticker, "error": str(e)})

        # Sort results highest score first
        results.sort(key=lambda x: x["surprise_score"], reverse=True)

        return {
            "status": "success",
            "processed_count": len(results),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scores": results,
            "errors": errors
        }

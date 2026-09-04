from datetime import datetime
from database import db
from models.user import UserInteraction, UserPreferenceWeights

class PersonalizationService:
    DEFAULT_WEIGHTS = {
        'volatility': 0.40,
        'volume': 0.30,
        'news': 0.20,
        'extreme': 0.10
    }

    @staticmethod
    def get_user_weights(user_id=1):
        """Fetches active user factor weights or initializes default baseline weights."""
        pref = UserPreferenceWeights.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreferenceWeights(
                user_id=user_id,
                volatility_weight=0.40,
                volume_weight=0.30,
                news_weight=0.20,
                extreme_weight=0.10
            )
            db.session.add(pref)
            db.session.commit()
        return pref

    @staticmethod
    def normalize_and_clamp_weights(vol_w, v_w, news_w, ext_w):
        """Clamps weights between [0.10, 0.50] and normalizes total sum to 1.0."""
        # 1. Clamp bounds
        vol_w = min(0.50, max(0.10, vol_w))
        v_w = min(0.50, max(0.10, v_w))
        news_w = min(0.50, max(0.10, news_w))
        ext_w = min(0.50, max(0.10, ext_w))

        # 2. Normalize to sum = 1.0
        total = vol_w + v_w + news_w + ext_w
        if total > 0:
            vol_w = round(vol_w / total, 3)
            v_w = round(v_w / total, 3)
            news_w = round(news_w / total, 3)
            ext_w = round(1.0 - (vol_w + v_w + news_w), 3) # ensure exact sum = 1.0

        return vol_w, v_w, news_w, ext_w

    @staticmethod
    def record_interaction(user_id=1, ticker='NVDA', interaction_type='news_clicked', event_type=None):
        """Logs user interaction feedback and dynamically shifts scoring factor weights."""
        # 1. Record interaction in database
        interaction = UserInteraction(
            user_id=user_id,
            ticker=ticker.upper(),
            interaction_type=interaction_type,
            event_type=event_type
        )
        db.session.add(interaction)

        # 2. Fetch current weights
        pref = PersonalizationService.get_user_weights(user_id=user_id)
        w_vol = pref.volatility_weight
        w_v = pref.volume_weight
        w_news = pref.news_weight
        w_ext = pref.extreme_weight

        explanation = ""

        # 3. Apply feedback adjustment rules
        if interaction_type in ['news_clicked', 'news_opened', 'more_news']:
            w_news += 0.05
            w_v -= 0.025
            w_vol -= 0.025
            explanation = "News interest signal recorded: News weight increased (+5%)."

        elif interaction_type in ['volume_ignored', 'volume_muted', 'less_volume']:
            w_v -= 0.05
            w_vol += 0.025
            w_news += 0.025
            explanation = "Volume mute signal recorded: Volume weight reduced (-5%)."

        elif interaction_type in ['volatility_expanded', 'price_focus']:
            w_vol += 0.05
            w_v -= 0.025
            w_ext -= 0.025
            explanation = "Price volatility focus recorded: Volatility weight increased (+5%)."

        # 4. Clamp & normalize
        w_vol, w_v, w_news, w_ext = PersonalizationService.normalize_and_clamp_weights(w_vol, w_v, w_news, w_ext)

        pref.volatility_weight = w_vol
        pref.volume_weight = w_v
        pref.news_weight = w_news
        pref.extreme_weight = w_ext
        pref.updated_at = datetime.utcnow()

        db.session.commit()

        # 5. Recalculate surprise scores using updated weights
        from services.surprise_service import SurpriseScoringService
        SurpriseScoringService.recalculate_all(user_id=user_id)

        return {
            "status": "success",
            "message": explanation or f"Interaction '{interaction_type}' recorded.",
            "weights": pref.to_dict()
        }

    @staticmethod
    def reset_user_weights(user_id=1):
        """Resets factor weights to baseline defaults (40/30/20/10)."""
        pref = PersonalizationService.get_user_weights(user_id=user_id)
        pref.volatility_weight = 0.40
        pref.volume_weight = 0.30
        pref.news_weight = 0.20
        pref.extreme_weight = 0.10
        pref.updated_at = datetime.utcnow()
        db.session.commit()

        # Recalculate scores
        from services.surprise_service import SurpriseScoringService
        SurpriseScoringService.recalculate_all(user_id=user_id)

        return {
            "status": "success",
            "message": "User weights reset to baseline defaults (40/30/20/10).",
            "weights": pref.to_dict()
        }

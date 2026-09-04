from datetime import datetime, timedelta
import json
from database import db
from models.user import UserLastSeen
from models.market import MarketEvent, NewsEvent
from models.watchlist import Watchlist, WatchlistStock
from models.surprise import ComputedSurpriseScore
from services.surprise_service import SurpriseScoringService

class CatchUpService:

    @staticmethod
    def get_digest_for_user(user_id=1, watchlist_id=1):
        """Generates prioritized 'While You Were Away' digest cards for events after last_seen_at."""
        
        # 1. Fetch UserLastSeen (default to 2 days ago if not set)
        last_seen_record = UserLastSeen.query.filter_by(user_id=user_id, watchlist_id=watchlist_id).first()
        if last_seen_record and last_seen_record.last_seen_at:
            last_seen_at = last_seen_record.last_seen_at
        else:
            last_seen_at = datetime.utcnow() - timedelta(days=2)

        now = datetime.utcnow()
        time_away_hours = round((now - last_seen_at).total_seconds() / 3600.0, 1)

        # 2. Get active watchlist stocks
        active_stocks = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, is_active=True).all()
        stock_map = {s.ticker: s.company_name for s in active_stocks}

        story_cards = []

        for ticker, company_name in stock_map.items():
            # Get latest market event after last_seen_at
            event = MarketEvent.query.filter(
                MarketEvent.ticker == ticker,
                MarketEvent.timestamp >= last_seen_at
            ).order_by(MarketEvent.timestamp.desc()).first()

            if not event:
                # Fallback to absolute latest event if no event in time window
                event = MarketEvent.query.filter_by(ticker=ticker)\
                    .order_by(MarketEvent.timestamp.desc()).first()

            if not event:
                continue

            # Ensure surprise score is calculated
            score_obj = ComputedSurpriseScore.query.filter_by(ticker=ticker, market_event_id=event.id).first()
            if not score_obj:
                score_dict = SurpriseScoringService.calculate_for_ticker(ticker)
            else:
                score_dict = score_obj.to_dict()

            # Check for recent news after last_seen_at
            news_items = NewsEvent.query.filter(
                NewsEvent.ticker == ticker,
                NewsEvent.published_at >= last_seen_at
            ).order_by(NewsEvent.published_at.desc()).all()

            # Metadata parsing for Abnormal Silence detection
            meta = event.get_metadata()
            tech_sector_change = meta.get("tech_sector_change_percent")
            sector_divergence = meta.get("sector_divergence", False)
            abnormal_silence_flag = meta.get("abnormal_silence_flag", False)

            # --- ABNORMAL SILENCE DETECTION ---
            # Condition: Stock moved <= 1.5% while sector moved >= 3.0%, OR high vol stock (stdDev >= 2.0%) moved <= 0.3%
            price_move = abs(event.price_change_percent or 0.0)
            is_abnormal_silence = False

            if abnormal_silence_flag or sector_divergence:
                is_abnormal_silence = True
            elif tech_sector_change and abs(tech_sector_change) >= 3.0 and price_move <= 1.5:
                is_abnormal_silence = True
            elif score_dict and score_dict.get("historical_std_dev", 0.0) >= 2.0 and price_move <= 0.3:
                is_abnormal_silence = True

            # --- STORY CARD CLASSIFICATION & PRIORITY ASSIGNMENT ---
            surprise_score = score_dict.get("surprise_score", 0) if score_dict else 0
            category = score_dict.get("category", "NORMAL") if score_dict else "NORMAL"

            if surprise_score >= 80:
                card_type = "ABNORMAL_MOVEMENT"
                priority = 1
                badge_text = "🚨 VERY UNUSUAL"
                badge_style = "rose"
            elif is_abnormal_silence:
                card_type = "ABNORMAL_SILENCE"
                priority = 2
                badge_text = "⚠ UNUSUALLY QUIET"
                badge_style = "amber"
            elif surprise_score >= 50:
                card_type = "MODERATE_MOVEMENT"
                priority = 3
                badge_text = "⚠️ UNUSUAL"
                badge_style = "amber"
            else:
                card_type = "NORMAL"
                priority = 4
                badge_text = "✓ NORMAL"
                badge_style = "emerald"

            # Construct human-readable story highlights
            highlights = []
            if event.price_change_percent is not None:
                direction = "Dropped" if event.price_change_percent < 0 else "Rose"
                highlights.append(f"{direction} {abs(event.price_change_percent):.1f}%.")

            if is_abnormal_silence:
                if tech_sector_change:
                    highlights.append(f"However, the technology sector rose approximately {tech_sector_change:.1f}%.")
                highlights.append("This unusually low movement relative to the sector may be worth investigating.")
            elif score_dict:
                for bullet in score_dict.get("explanation_factors", []):
                    # Avoid repeating raw % move
                    if "% price move" not in bullet:
                        highlights.append(bullet + ".")

            if card_type == "NORMAL" and not is_abnormal_silence:
                highlights = [
                    f"{'Dropped' if event.price_change_percent < 0 else 'Moved'} {abs(event.price_change_percent or 0):.1f}%.",
                    "This movement is within its normal historical range.",
                    "No major event detected."
                ]

            news_headline = news_items[0].headline if news_items else None

            story_cards.append({
                "ticker": ticker,
                "company_name": company_name,
                "card_type": card_type,
                "priority": priority,
                "badge_text": badge_text,
                "badge_style": badge_style,
                "surprise_score": surprise_score,
                "price": event.price,
                "price_change_percent": event.price_change_percent,
                "volume": event.volume,
                "volume_ratio": score_dict.get("volume_ratio", 1.0) if score_dict else 1.0,
                "highlights": highlights,
                "news_headline": news_headline,
                "is_abnormal_silence": is_abnormal_silence,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None
            })

        # 3. Sort story cards by priority (Priority 1 -> 2 -> 3 -> 4)
        story_cards.sort(key=lambda x: (x["priority"], -x["surprise_score"]))

        # 4. Limit to top 3 to 6 prioritized events
        prioritized_cards = story_cards[:6]

        return {
            "status": "success",
            "last_seen_at": last_seen_at.isoformat() + "Z",
            "time_away_hours": time_away_hours,
            "total_watchlist_count": len(active_stocks),
            "digest_cards_count": len(prioritized_cards),
            "story_cards": prioritized_cards
        }

    @staticmethod
    def update_last_seen(user_id=1, watchlist_id=1):
        """Updates last_seen_at timestamp for user to current time."""
        now = datetime.utcnow()
        record = UserLastSeen.query.filter_by(user_id=user_id, watchlist_id=watchlist_id).first()
        if not record:
            record = UserLastSeen(user_id=user_id, watchlist_id=watchlist_id, last_seen_at=now)
            db.session.add(record)
        else:
            record.last_seen_at = now
            record.updated_at = now

        db.session.commit()
        return {
            "status": "success",
            "message": "Last-seen timestamp updated to current time.",
            "last_seen_at": now.isoformat() + "Z"
        }

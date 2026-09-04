from datetime import datetime
import json
from models.market import MarketEvent, DataSource
from models.watchlist import WatchlistStock

class DataTrustService:

    @staticmethod
    def evaluate_event_trust(event):
        """Evaluates data freshness, age, volume thinness, and source conflict for a MarketEvent."""
        if not event:
            return None

        now = datetime.utcnow()
        event_time = event.source_timestamp or event.timestamp
        age_minutes = round(max(0, (now - event_time).total_seconds() / 60.0), 1)

        # Parse metadata
        meta = event.get_metadata()
        secondary_source = meta.get("secondary_source")
        secondary_price = meta.get("secondary_price")
        is_stale_flag = meta.get("is_stale", False)
        staleness_reason = meta.get("staleness_reason")

        # --- 1. FRESHNESS CLASSIFICATION ---
        if is_stale_flag or age_minutes >= 60:
            hours_ago = round(age_minutes / 60.0, 1)
            freshness_label = staleness_reason or f"Data from {hours_ago} hours ago"
            freshness_code = "STALE"
            badge_color = "amber"
        elif age_minutes >= 5:
            freshness_label = f"Delayed {int(age_minutes)} min"
            freshness_code = "DELAYED"
            badge_color = "amber"
        else:
            freshness_label = "Live"
            freshness_code = "LIVE"
            badge_color = "emerald"

        # --- 2. THIN VOLUME DETECTION ---
        is_thin_volume = False
        if event.average_volume and event.volume:
            if event.volume < (0.3 * event.average_volume):
                is_thin_volume = True

        # --- 3. SOURCE CONFLICT DETECTION ---
        has_conflict = False
        conflict_percent = 0.0
        primary_price = event.price

        if secondary_price and primary_price > 0:
            diff = abs(primary_price - secondary_price)
            conflict_percent = round((diff / primary_price) * 100.0, 2)
            if conflict_percent >= 0.5:
                has_conflict = True

        if event.freshness_status == 'conflicting':
            has_conflict = True
            if conflict_percent == 0.0 and meta.get("conflict_percent"):
                conflict_percent = meta.get("conflict_percent")

        # Determine overall trust badge to display
        if has_conflict:
            badge_text = f"⚠ Sources differ by {conflict_percent}%"
            badge_style = "amber"
        elif is_thin_volume:
            badge_text = "Thin volume"
            badge_style = "cyan"
        else:
            badge_text = freshness_label
            badge_style = badge_color

        return {
            "market_event_id": event.id,
            "ticker": event.ticker,
            "source": event.source,
            "secondary_source": secondary_source,
            "primary_price": primary_price,
            "secondary_price": secondary_price,
            "age_minutes": age_minutes,
            "freshness_code": freshness_code,
            "freshness_label": freshness_label,
            "is_thin_volume": is_thin_volume,
            "has_conflict": has_conflict,
            "conflict_percent": conflict_percent,
            "badge_text": badge_text,
            "badge_style": badge_style
        }

    @staticmethod
    def get_watchlist_trust_summary(watchlist_id=1):
        """Scans all active watchlist stocks and returns trust status, warnings, and active conflicts."""
        active_stocks = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, is_active=True).all()
        stock_trust_list = []
        conflicts_list = []
        stale_count = 0
        live_count = 0
        conflict_count = 0

        for stock in active_stocks:
            latest_event = MarketEvent.query.filter_by(ticker=stock.ticker)\
                .order_by(MarketEvent.timestamp.desc()).first()

            if latest_event:
                trust_info = DataTrustService.evaluate_event_trust(latest_event)
                stock_trust_list.append(trust_info)

                if trust_info["has_conflict"]:
                    conflict_count += 1
                    conflicts_list.append(trust_info)

                if trust_info["freshness_code"] in ["STALE", "DELAYED"]:
                    stale_count += 1
                else:
                    live_count += 1

        return {
            "status": "success",
            "total_monitored": len(active_stocks),
            "live_count": live_count,
            "stale_count": stale_count,
            "conflict_count": conflict_count,
            "stock_trust": stock_trust_list,
            "active_conflicts": conflicts_list
        }

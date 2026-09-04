import random
from datetime import datetime, timedelta
import json
from database import db
from models.user import User, UserLastSeen
from models.watchlist import Watchlist, WatchlistStock
from models.market import MarketEvent, NewsEvent, DataSource

class MockDataService:
    STOCKS_DATA = [
        {"ticker": "NVDA", "name": "NVIDIA Corporation", "base_price": 140.0, "avg_vol": 50000000, "daily_volatility": 0.025},
        {"ticker": "AAPL", "name": "Apple Inc.", "base_price": 220.0, "avg_vol": 48000000, "daily_volatility": 0.012},
        {"ticker": "TSLA", "name": "Tesla Inc.", "base_price": 240.0, "avg_vol": 62000000, "daily_volatility": 0.035},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "base_price": 440.0, "avg_vol": 21000000, "daily_volatility": 0.011},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "base_price": 185.0, "avg_vol": 38000000, "daily_volatility": 0.015},
    ]

    @staticmethod
    def seed_initial_data():
        """Resets DB and generates deterministic 60-day historical data per stock."""
        db.drop_all()
        db.create_all()

        # 1. Create Demo User
        user = User(username='demo_user')
        db.session.add(user)
        db.session.commit()

        # 2. Create Watchlist
        watchlist = Watchlist(user_id=user.id, name='Hackathon Watchlist')
        db.session.add(watchlist)
        db.session.commit()

        # 3. Add Watchlist Stocks
        for s in MockDataService.STOCKS_DATA:
            stock = WatchlistStock(
                watchlist_id=watchlist.id,
                ticker=s["ticker"],
                company_name=s["name"],
                is_active=True
            )
            db.session.add(stock)

        # 4. Create Data Sources
        ds1 = DataSource(name='PrimaryFeed', source_type='real_time_exchange')
        ds2 = DataSource(name='SecondaryFeed', source_type='delayed_feed')
        ds3 = DataSource(name='TechNewsWire', source_type='news_wire')
        db.session.add_all([ds1, ds2, ds3])
        db.session.commit()

        # 5. Set UserLastSeen (2 days ago to simulate user being away)
        last_seen_time = datetime.utcnow() - timedelta(days=2)
        user_last_seen = UserLastSeen(
            user_id=user.id,
            watchlist_id=watchlist.id,
            last_seen_at=last_seen_time
        )
        db.session.add(user_last_seen)

        # 6. Seed 60 Historical Days per Stock (Deterministic using Random seed)
        rng = random.Random(42)
        now = datetime.utcnow()
        start_date = now - timedelta(days=62)

        for stock in MockDataService.STOCKS_DATA:
            ticker = stock["ticker"]
            price = stock["base_price"]
            avg_vol = stock["avg_vol"]
            volatility = stock["daily_volatility"]

            for day_offset in range(60):
                event_time = start_date + timedelta(days=day_offset, hours=9, minutes=30)
                
                # Calculate small realistic price change
                pct_change = rng.gauss(0, volatility)
                prev_price = price
                price = max(1.0, round(prev_price * (1 + pct_change), 2))
                actual_change_pct = round(((price - prev_price) / prev_price) * 100, 2)
                
                # Volume fluctuate around avg_vol
                volume = int(avg_vol * rng.uniform(0.7, 1.3))

                m_event = MarketEvent(
                    ticker=ticker,
                    event_type='price_update',
                    price=price,
                    previous_price=prev_price,
                    price_change_percent=actual_change_pct,
                    volume=volume,
                    average_volume=avg_vol,
                    timestamp=event_time,
                    source='PrimaryFeed',
                    source_timestamp=event_time,
                    freshness_status='live',
                    metadata_json=json.dumps({"historical_day": day_offset + 1})
                )
                db.session.add(m_event)

        db.session.commit()

        # Recalculate Surprise Scores automatically
        from services.surprise_service import SurpriseScoringService
        SurpriseScoringService.recalculate_all()

        return {
            "status": "success",
            "message": "Database reset, seeded with 60 days of historical data (300 observations), and Surprise Scores calculated."
        }

    @staticmethod
    def run_demo_scenario():
        """Appends post-last-seen market and news events simulating user absence."""
        now = datetime.utcnow()
        recent_time = now - timedelta(hours=3)

        # NVDA: Drop 6.2%, 3.1x volume spike, negative news
        nvda_event = MarketEvent(
            ticker='NVDA',
            event_type='price_update',
            price=131.32,
            previous_price=140.00,
            price_change_percent=-6.20,
            volume=155000000,
            average_volume=50000000,
            timestamp=recent_time,
            source='PrimaryFeed',
            source_timestamp=recent_time,
            freshness_status='live',
            metadata_json=json.dumps({
                "volume_ratio": 3.1,
                "is_40_day_extreme": True
            })
        )
        nvda_news = NewsEvent(
            ticker='NVDA',
            headline='NVIDIA Faces Supply Chain Disruptions & Lowers Q4 Guidance',
            summary='Key semiconductor supply bottlenecks impact current quarter production targets.',
            source='TechNewsWire',
            published_at=recent_time - timedelta(minutes=45),
            sentiment='negative',
            event_type='earnings_guidance'
        )

        # AAPL: Quiet move (+1.1%) despite tech sector surge (+4.0%)
        aapl_event = MarketEvent(
            ticker='AAPL',
            event_type='price_update',
            price=222.42,
            previous_price=220.00,
            price_change_percent=1.10,
            volume=48000000,
            average_volume=50000000,
            timestamp=recent_time,
            source='PrimaryFeed',
            source_timestamp=recent_time,
            freshness_status='live',
            metadata_json=json.dumps({
                "tech_sector_change_percent": 4.0,
                "sector_divergence": True,
                "abnormal_silence_flag": True
            })
        )

        # TSLA: Normal movement (-1.2%)
        tsla_event = MarketEvent(
            ticker='TSLA',
            event_type='price_update',
            price=237.12,
            previous_price=240.00,
            price_change_percent=-1.20,
            volume=60000000,
            average_volume=62000000,
            timestamp=recent_time,
            source='PrimaryFeed',
            source_timestamp=recent_time,
            freshness_status='live'
        )

        # MSFT: Minor move (+0.4%)
        msft_event = MarketEvent(
            ticker='MSFT',
            event_type='price_update',
            price=441.76,
            previous_price=440.00,
            price_change_percent=0.40,
            volume=20000000,
            average_volume=21000000,
            timestamp=recent_time,
            source='PrimaryFeed',
            source_timestamp=recent_time,
            freshness_status='live'
        )

        # AMZN: Data quality conflict & stale data scenario
        amzn_event = MarketEvent(
            ticker='AMZN',
            event_type='price_update',
            price=183.52,
            previous_price=185.00,
            price_change_percent=-0.80,
            volume=38000000,
            average_volume=38000000,
            timestamp=recent_time - timedelta(hours=2),
            source='PrimaryFeed',
            source_timestamp=recent_time - timedelta(hours=2),
            freshness_status='conflicting',
            metadata_json=json.dumps({
                "secondary_source": "SecondaryFeed",
                "secondary_price": 184.85,
                "conflict_percent": 0.72,
                "is_stale": True,
                "staleness_reason": "Data from 2 hours ago"
            })
        )
        amzn_news = NewsEvent(
            ticker='AMZN',
            headline='Amazon Web Services Expands Cloud Infrastructure in Europe',
            summary='AWS announces new data center investments across major European hubs.',
            source='TechNewsWire',
            published_at=recent_time - timedelta(hours=1),
            sentiment='positive',
            event_type='expansion_announcement'
        )

        db.session.add_all([nvda_event, nvda_news, aapl_event, tsla_event, msft_event, amzn_event, amzn_news])
        db.session.commit()

        # Recalculate Surprise Scores automatically after demo run
        from services.surprise_service import SurpriseScoringService
        SurpriseScoringService.recalculate_all()

        return {
            "status": "success",
            "message": "Demo scenario events appended and Surprise Scores recalculated dynamically."
        }

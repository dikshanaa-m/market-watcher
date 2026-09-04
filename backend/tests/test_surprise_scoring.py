import unittest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.market import MarketEvent, NewsEvent
from services.surprise_service import SurpriseScoringService
from datetime import datetime, timedelta

class TestSurpriseScoringService(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_1_same_move_different_volatility(self):
        """Stock A (low vol 1%) vs Stock B (high vol 4%) experiencing the exact same 4% price change."""
        now = datetime.utcnow()
        
        # Stock A: historical volatility ~ 1.0%
        stk_a_changes = [1.0, -0.8, 1.2, -1.0, 0.9, -1.1, 0.8, -1.0, 1.0, -0.9]
        for i, chg in enumerate(stk_a_changes):
            db.session.add(MarketEvent(
                ticker='STKA', event_type='price_update', price=100.0,
                price_change_percent=chg,
                volume=1000000, timestamp=now - timedelta(days=20 - i)
            ))
            
        # Stock B: historical volatility ~ 4.0%
        stk_b_changes = [4.0, -3.8, 4.2, -4.0, 3.9, -4.1, 3.8, -4.0, 4.0, -3.9]
        for i, chg in enumerate(stk_b_changes):
            db.session.add(MarketEvent(
                ticker='STKB', event_type='price_update', price=100.0,
                price_change_percent=chg,
                volume=1000000, timestamp=now - timedelta(days=20 - i)
            ))

        # Latest event for both: +4.0% move
        db.session.add(MarketEvent(
            ticker='STKA', event_type='price_update', price=104.0,
            price_change_percent=4.0, volume=1000000, timestamp=now
        ))
        db.session.add(MarketEvent(
            ticker='STKB', event_type='price_update', price=104.0,
            price_change_percent=4.0, volume=1000000, timestamp=now
        ))
        db.session.commit()

        score_a = SurpriseScoringService.calculate_for_ticker('STKA')
        score_b = SurpriseScoringService.calculate_for_ticker('STKB')

        # Stock A (low vol) must have significantly higher volatility z-score & score than Stock B
        self.assertGreater(score_a['volatility_z_score'], score_b['volatility_z_score'])
        self.assertGreater(score_a['volatility_score'], score_b['volatility_score'])
        self.assertGreater(score_a['surprise_score'], score_b['surprise_score'])

    def test_2_volume_spike_progression(self):
        """Verify 1.0x volume < 2.0x volume < 3.0x volume in volume score."""
        now = datetime.utcnow()
        for i in range(10):
            db.session.add(MarketEvent(
                ticker='VOL1', event_type='price_update', price=100.0, price_change_percent=0.5,
                volume=1000000, timestamp=now - timedelta(days=20 - i)
            ))
        
        # Latest event with 1.0x volume
        db.session.add(MarketEvent(ticker='VOL1', event_type='price_update', price=100.5, price_change_percent=0.5, volume=1000000, timestamp=now))
        db.session.commit()
        score_1x = SurpriseScoringService.calculate_for_ticker('VOL1')

        # Update latest event volume to 2.0x
        latest = MarketEvent.query.filter_by(ticker='VOL1').order_by(MarketEvent.timestamp.desc()).first()
        latest.volume = 2000000
        db.session.commit()
        score_2x = SurpriseScoringService.calculate_for_ticker('VOL1')

        # Update latest event volume to 3.0x
        latest.volume = 3000000
        db.session.commit()
        score_3x = SurpriseScoringService.calculate_for_ticker('VOL1')

        self.assertLess(score_1x['volume_score'], score_2x['volume_score'])
        self.assertLess(score_2x['volume_score'], score_3x['volume_score'])

    def test_3_normal_movement_low_score(self):
        """A small move within the stock's historical range produces a low score."""
        now = datetime.utcnow()
        for i in range(10):
            db.session.add(MarketEvent(
                ticker='NORM', event_type='price_update', price=100.0,
                price_change_percent=2.0 if i % 2 == 0 else -2.0,
                volume=1000000, timestamp=now - timedelta(days=20 - i)
            ))
            
        # Small move +0.2% with normal volume
        db.session.add(MarketEvent(
            ticker='NORM', event_type='price_update', price=100.2,
            price_change_percent=0.2, volume=1000000, timestamp=now
        ))
        db.session.commit()

        score = SurpriseScoringService.calculate_for_ticker('NORM')
        self.assertEqual(score['category'], 'NORMAL')
        self.assertLessEqual(score['surprise_score'], 24)

    def test_4_score_bounds_clamped(self):
        """Verify 0 <= final_score <= 100 for extreme high and low scenarios."""
        now = datetime.utcnow()
        # Extreme high: huge drop -50%, massive volume 10x, negative news
        db.session.add(MarketEvent(ticker='EXTR', event_type='price_update', price=100.0, price_change_percent=1.0, volume=1000000, timestamp=now - timedelta(days=1)))
        db.session.add(MarketEvent(ticker='EXTR', event_type='price_update', price=50.0, price_change_percent=-50.0, volume=10000000, timestamp=now))
        db.session.add(NewsEvent(ticker='EXTR', headline='Catastrophic Loss', source='TechNewsWire', sentiment='negative', published_at=now))
        db.session.commit()

        score = SurpriseScoringService.calculate_for_ticker('EXTR')
        self.assertGreaterEqual(score['surprise_score'], 0)
        self.assertLessEqual(score['surprise_score'], 100)

    def test_5_determinism(self):
        """Running the calculation twice against unchanged data produces identical scores."""
        now = datetime.utcnow()
        db.session.add(MarketEvent(ticker='DET', event_type='price_update', price=100.0, price_change_percent=1.0, volume=1000000, timestamp=now - timedelta(days=1)))
        db.session.add(MarketEvent(ticker='DET', event_type='price_update', price=105.0, price_change_percent=5.0, volume=2000000, timestamp=now))
        db.session.commit()

        run1 = SurpriseScoringService.calculate_for_ticker('DET')
        run2 = SurpriseScoringService.calculate_for_ticker('DET')
        self.assertEqual(run1['surprise_score'], run2['surprise_score'])
        self.assertEqual(run1['category'], run2['category'])

    def test_6_no_historical_data_safety(self):
        """Service gracefully handles single observation without crashing."""
        now = datetime.utcnow()
        db.session.add(MarketEvent(ticker='SOLO', event_type='price_update', price=100.0, price_change_percent=1.5, volume=1000000, timestamp=now))
        db.session.commit()

        score = SurpriseScoringService.calculate_for_ticker('SOLO')
        self.assertIsNotNone(score)
        self.assertIn('surprise_score', score)

if __name__ == '__main__':
    unittest.main()

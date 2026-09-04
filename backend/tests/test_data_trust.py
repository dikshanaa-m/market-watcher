import unittest
import os
import sys
import json

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.market import MarketEvent
from services.data_trust_service import DataTrustService
from datetime import datetime, timedelta

class TestDataTrust(unittest.TestCase):
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

    def test_1_freshness_live_delayed_stale(self):
        """Verify Live, Delayed, and Stale badge classification."""
        now = datetime.utcnow()
        
        # Live event (2 mins old)
        live_evt = MarketEvent(ticker='LIVE1', event_type='price_update', price=100.0, volume=1000000, timestamp=now - timedelta(minutes=2))
        
        # Delayed event (15 mins old)
        delayed_evt = MarketEvent(ticker='DEL1', event_type='price_update', price=100.0, volume=1000000, timestamp=now - timedelta(minutes=15))

        # Stale event (2.5 hours old)
        stale_evt = MarketEvent(ticker='STL1', event_type='price_update', price=100.0, volume=1000000, timestamp=now - timedelta(hours=2.5))

        db.session.add_all([live_evt, delayed_evt, stale_evt])
        db.session.commit()

        eval_live = DataTrustService.evaluate_event_trust(live_evt)
        eval_del = DataTrustService.evaluate_event_trust(delayed_evt)
        eval_stl = DataTrustService.evaluate_event_trust(stale_evt)

        self.assertEqual(eval_live['freshness_code'], 'LIVE')
        self.assertEqual(eval_del['freshness_code'], 'DELAYED')
        self.assertEqual(eval_stl['freshness_code'], 'STALE')

    def test_2_source_price_conflict_detection(self):
        """Verify source conflict detection when primary and secondary feeds differ by >= 0.5%."""
        now = datetime.utcnow()
        conflict_evt = MarketEvent(
            ticker='AMZN',
            event_type='price_update',
            price=183.52, # PrimaryFeed
            volume=38000000,
            timestamp=now,
            source='PrimaryFeed',
            freshness_status='conflicting',
            metadata_json=json.dumps({
                "secondary_source": "SecondaryFeed",
                "secondary_price": 184.85, # Mismatch 0.72%
                "conflict_percent": 0.72
            })
        )
        db.session.add(conflict_evt)
        db.session.commit()

        eval_res = DataTrustService.evaluate_event_trust(conflict_evt)
        self.assertTrue(eval_res['has_conflict'])
        self.assertEqual(eval_res['conflict_percent'], 0.72)
        self.assertIn("Sources differ by 0.72%", eval_res['badge_text'])

    def test_3_thin_volume_detection(self):
        """Verify thin volume flag when volume < 0.3 * average_volume."""
        now = datetime.utcnow()
        thin_evt = MarketEvent(
            ticker='THIN1', event_type='price_update', price=50.0,
            volume=100000, average_volume=1000000, # 10% of avg volume
            timestamp=now
        )
        db.session.add(thin_evt)
        db.session.commit()

        eval_res = DataTrustService.evaluate_event_trust(thin_evt)
        self.assertTrue(eval_res['is_thin_volume'])
        self.assertEqual(eval_res['badge_text'], "Thin volume")

if __name__ == '__main__':
    unittest.main()

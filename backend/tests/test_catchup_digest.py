import unittest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.user import User, UserLastSeen
from models.watchlist import Watchlist, WatchlistStock
from models.market import MarketEvent, NewsEvent
from services.catchup_service import CatchUpService
from services.mock_data_service import MockDataService
from datetime import datetime, timedelta

class TestCatchUpDigest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        MockDataService.seed_initial_data()
        MockDataService.run_demo_scenario()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_1_digest_generation_and_size_limit(self):
        """Verify digest generates between 3 and 6 prioritized story cards."""
        digest = CatchUpService.get_digest_for_user(user_id=1, watchlist_id=1)
        self.assertEqual(digest['status'], 'success')
        self.assertGreaterEqual(digest['digest_cards_count'], 3)
        self.assertLessEqual(digest['digest_cards_count'], 6)

    def test_2_abnormal_movement_priority_1(self):
        """Verify NVDA is ranked #1 with ABNORMAL_MOVEMENT card_type."""
        digest = CatchUpService.get_digest_for_user(user_id=1, watchlist_id=1)
        cards = digest['story_cards']
        top_card = cards[0]
        self.assertEqual(top_card['ticker'], 'NVDA')
        self.assertEqual(top_card['card_type'], 'ABNORMAL_MOVEMENT')
        self.assertGreaterEqual(top_card['surprise_score'], 80)

    def test_3_abnormal_silence_detection(self):
        """Verify AAPL is detected as ABNORMAL_SILENCE due to sector divergence."""
        digest = CatchUpService.get_digest_for_user(user_id=1, watchlist_id=1)
        cards = digest['story_cards']
        aapl_card = next((c for c in cards if c['ticker'] == 'AAPL'), None)
        self.assertIsNotNone(aapl_card)
        self.assertTrue(aapl_card['is_abnormal_silence'])
        self.assertEqual(aapl_card['card_type'], 'ABNORMAL_SILENCE')
        self.assertEqual(aapl_card['badge_text'], '⚠ UNUSUALLY QUIET')

    def test_4_last_seen_timestamp_update(self):
        """Verify updating last-seen timestamp updates UserLastSeen in DB."""
        old_digest = CatchUpService.get_digest_for_user(user_id=1, watchlist_id=1)
        res = CatchUpService.update_last_seen(user_id=1, watchlist_id=1)
        self.assertEqual(res['status'], 'success')
        
        record = UserLastSeen.query.filter_by(user_id=1, watchlist_id=1).first()
        self.assertIsNotNone(record)
        self.assertIsNotNone(record.last_seen_at)

if __name__ == '__main__':
    unittest.main()

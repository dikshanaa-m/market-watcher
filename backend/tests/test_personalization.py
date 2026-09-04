import unittest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.user import User, UserPreferenceWeights, UserInteraction
from services.personalization_service import PersonalizationService
from services.mock_data_service import MockDataService

class TestPersonalization(unittest.TestCase):
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

    def test_1_baseline_weights(self):
        """Verify initial default weights are 40% Volatility, 30% Volume, 20% News, 10% Extreme."""
        pref = PersonalizationService.get_user_weights(user_id=1)
        self.assertEqual(pref.volatility_weight, 0.40)
        self.assertEqual(pref.volume_weight, 0.30)
        self.assertEqual(pref.news_weight, 0.20)
        self.assertEqual(pref.extreme_weight, 0.10)

    def test_2_news_interest_increases_news_weight(self):
        """Verify news_clicked interaction increases news weight."""
        res = PersonalizationService.record_interaction(user_id=1, ticker='NVDA', interaction_type='news_clicked')
        self.assertEqual(res['status'], 'success')
        
        pref = PersonalizationService.get_user_weights(user_id=1)
        self.assertGreater(pref.news_weight, 0.20)
        self.assertAlmostEqual(pref.volatility_weight + pref.volume_weight + pref.news_weight + pref.extreme_weight, 1.0, places=2)

    def test_3_volume_mute_decreases_volume_weight(self):
        """Verify volume_ignored interaction decreases volume weight."""
        res = PersonalizationService.record_interaction(user_id=1, ticker='NVDA', interaction_type='volume_ignored')
        self.assertEqual(res['status'], 'success')

        pref = PersonalizationService.get_user_weights(user_id=1)
        self.assertLess(pref.volume_weight, 0.30)
        self.assertAlmostEqual(pref.volatility_weight + pref.volume_weight + pref.news_weight + pref.extreme_weight, 1.0, places=2)

    def test_4_reset_weights(self):
        """Verify reset_user_weights restores 40/30/20/10 default baseline."""
        PersonalizationService.record_interaction(user_id=1, ticker='NVDA', interaction_type='news_clicked')
        res = PersonalizationService.reset_user_weights(user_id=1)
        self.assertEqual(res['status'], 'success')

        pref = PersonalizationService.get_user_weights(user_id=1)
        self.assertEqual(pref.volatility_weight, 0.40)
        self.assertEqual(pref.volume_weight, 0.30)
        self.assertEqual(pref.news_weight, 0.20)
        self.assertEqual(pref.extreme_weight, 0.10)

if __name__ == '__main__':
    unittest.main()

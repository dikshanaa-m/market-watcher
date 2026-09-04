import unittest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.user import User, UserLastSeen, UserPreferenceWeights, UserInteraction
from models.watchlist import Watchlist, WatchlistStock
from models.market import MarketEvent, NewsEvent
from models.surprise import ComputedSurpriseScore
from services.ai_explanation_service import AIExplanationService
from services.mock_data_service import MockDataService


class TestAIExplanation(unittest.TestCase):
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

    def test_1_extract_structured_facts(self):
        """Verify structured facts extraction for seeded stock (NVDA)."""
        facts = AIExplanationService.extract_structured_facts("NVDA")
        self.assertIsNotNone(facts)
        self.assertEqual(facts["ticker"], "NVDA")
        self.assertIn("price_change_percent", facts)
        self.assertIn("surprise_score", facts)
        self.assertIn("volatility_z_score", facts)

    def test_2_deterministic_explanation_fallback(self):
        """Verify clean 1-2 sentence explanation is generated without GEMINI_API_KEY."""
        res = AIExplanationService.generate_explanation("NVDA")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["provider"], "fallback_rule_engine")
        self.assertIn("NVDA", res["explanation"])
        self.assertTrue(len(res["explanation"]) > 20)

    def test_3_ai_explanation_api_route(self):
        """Verify GET /api/ai/explain/NVDA route works as expected."""
        client = app.test_client()
        response = client.get('/api/ai/explain/NVDA')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["ticker"], "NVDA")
        self.assertIn("explanation", data)

    def test_4_explain_digest_api_route(self):
        """Verify POST /api/ai/explain-digest route works for multiple tickers."""
        client = app.test_client()
        response = client.post('/api/ai/explain-digest', json={"tickers": ["NVDA", "AAPL"]})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("NVDA", data["explanations"])
        self.assertIn("AAPL", data["explanations"])

if __name__ == '__main__':
    unittest.main()

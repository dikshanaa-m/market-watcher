import os
import json
import urllib.request
from models.market import MarketEvent, NewsEvent
from models.watchlist import WatchlistStock
from models.surprise import ComputedSurpriseScore
from services.surprise_service import SurpriseScoringService

class AIExplanationService:

    @staticmethod
    def extract_structured_facts(ticker):
        ticker = ticker.upper()
        
        # 1. Fetch Stock Name
        stock = WatchlistStock.query.filter_by(ticker=ticker).first()
        company_name = stock.company_name if stock else ticker

        # 2. Fetch Latest Market Event
        event = MarketEvent.query.filter_by(ticker=ticker)\
            .order_by(MarketEvent.timestamp.desc()).first()
            
        if not event:
            return None

        # 3. Fetch Computed Surprise Score
        score_obj = ComputedSurpriseScore.query.filter_by(ticker=ticker, market_event_id=event.id).first()
        if not score_obj:
            score_dict = SurpriseScoringService.calculate_for_ticker(ticker) or {}
        else:
            score_dict = score_obj.to_dict()

        # 4. Fetch News Event
        news = NewsEvent.query.filter_by(ticker=ticker)\
            .order_by(NewsEvent.published_at.desc()).first()

        meta = event.get_metadata()
        tech_sector_change = meta.get("tech_sector_change_percent")

        return {
            "ticker": ticker,
            "company_name": company_name,
            "price": event.price,
            "price_change_percent": event.price_change_percent,
            "volume": event.volume,
            "volume_ratio": score_dict.get("volume_ratio", 1.0),
            "historical_std_dev": score_dict.get("historical_std_dev", 0.0),
            "volatility_z_score": score_dict.get("volatility_z_score", 0.0),
            "surprise_score": score_dict.get("surprise_score", 0),
            "category": score_dict.get("category", "NORMAL"),
            "historical_extreme_percentile": score_dict.get("historical_extreme_percentile", 50.0),
            "news_headline": news.headline if news else None,
            "news_sentiment": news.sentiment if news else None,
            "tech_sector_change_percent": tech_sector_change,
            "explanation_bullets": score_dict.get("explanation_factors", [])
        }

    @staticmethod
    def generate_deterministic_explanation(facts):
        """Produces a clean 1-2 sentence human summary strictly from structured facts without AI key."""
        if not facts:
            return "No market facts available for explanation."

        ticker = facts["ticker"]
        company = facts["company_name"]
        change = facts["price_change_percent"]
        vol_ratio = facts["volume_ratio"]
        std_dev = facts["historical_std_dev"]
        news_headline = facts.get("news_headline")
        category = facts["category"]
        sector_change = facts.get("tech_sector_change_percent")

        direction = "dropped" if change < 0 else "rose"
        abs_change = abs(change or 0.0)

        # Clause 1: Price and Volatility
        if std_dev > 0:
            vol_multiple = round(abs_change / std_dev, 1)
            clause1 = f"{ticker} ({company}) {direction} {abs_change:.1f}%, moving {vol_multiple}× its normal daily volatility of {std_dev:.1f}%."
        else:
            clause1 = f"{ticker} ({company}) {direction} {abs_change:.1f}%."

        # Clause 2: Volume and News / Sector
        clause2 = ""
        if category == "VERY UNUSUAL" or vol_ratio >= 2.0:
            if news_headline:
                clause2 = f" Trading volume surged to {vol_ratio:.1f}× normal levels alongside news: '{news_headline}'."
            else:
                clause2 = f" Trading volume reached {vol_ratio:.1f}× its 60-day average."
        elif sector_change and abs_change <= 1.5:
            clause2 = f" Unusually quiet move despite the tech sector surging {sector_change:+.1f}%."
        elif news_headline:
            clause2 = f" News noted: '{news_headline}'."
        else:
            clause2 = " Price movement and trading volume remained within normal baseline expectations."

        return clause1 + clause2

    @staticmethod
    def generate_explanation(ticker):
        """Generates modular AI explanation payload using Gemini API if key exists, or deterministic fallback."""
        facts = AIExplanationService.extract_structured_facts(ticker)
        if not facts:
            return {"status": "error", "message": f"No facts found for ticker {ticker}"}

        api_key = os.getenv("GEMINI_API_KEY")
        provider = "fallback_rule_engine"

        if api_key:
            try:
                # Call Gemini API via REST payload
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                prompt = (
                    "You are an auditable financial fact explainer for Market Watcher. "
                    "Summarize ONLY the following structured facts into a clear 1-2 sentence human explanation. "
                    "Do NOT invent external facts, macro news, or speculation not listed. "
                    f"Facts: {json.dumps(facts)}"
                )
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                resp = urllib.request.urlopen(req, timeout=5)
                data = json.loads(resp.read().decode())
                
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if ai_text:
                    explanation_text = ai_text
                    provider = "gemini_ai"
                else:
                    explanation_text = AIExplanationService.generate_deterministic_explanation(facts)
            except Exception as e:
                print(f"[AI Explainer Fallback] Gemini API call error: {e}")
                explanation_text = AIExplanationService.generate_deterministic_explanation(facts)
        else:
            explanation_text = AIExplanationService.generate_deterministic_explanation(facts)

        return {
            "status": "success",
            "ticker": ticker,
            "provider": provider,
            "provider_label": "✨ Gemini 1.5 AI Model" if provider == "gemini_ai" else "⚙️ Structured Fact Engine",
            "explanation": explanation_text,
            "structured_facts": facts
        }

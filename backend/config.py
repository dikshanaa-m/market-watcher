import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 5000))
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-market-watcher")
    
    # SQLAlchemy configuration with SQLite fallback if PostgreSQL DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "market_watcher.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

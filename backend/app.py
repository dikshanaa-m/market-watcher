from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
from config import Config
from database import db
from routes.watchlist_routes import watchlist_bp
from routes.market_routes import market_bp
from routes.demo_routes import demo_bp
from routes.surprise_routes import surprise_bp
from routes.catchup_routes import catchup_bp
from routes.trust_routes import trust_bp
from routes.personalization_routes import personalization_bp
from routes.ai_routes import ai_bp
from services.mock_data_service import MockDataService
from services.surprise_service import SurpriseScoringService

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for all frontend origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SQLAlchemy DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(watchlist_bp)
app.register_blueprint(market_bp)
app.register_blueprint(demo_bp)
app.register_blueprint(surprise_bp)
app.register_blueprint(catchup_bp)
app.register_blueprint(trust_bp)
app.register_blueprint(personalization_bp)
app.register_blueprint(ai_bp)


# Auto-initialize database & seed default data if DB is fresh
with app.app_context():
    try:
        db.create_all()
        # Seed if no users exist
        from models.user import User
        if not User.query.first():
            print("[Market Watcher] Fresh database detected. Seeding 60-day historical mock data...")
            MockDataService.seed_initial_data()
            SurpriseScoringService.recalculate_all()
    except Exception as e:
        print(f"[Market Watcher DB Error] Could not initialize database: {e}")

@app.route("/api/health", methods=["GET"])
def health_check():
    # Verify DB connectivity
    db_status = "connected"
    try:
        from models.user import User
        User.query.first()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok",
        "service": "Market Watcher API",
        "message": "Market Watcher Backend API is active and operational",
        "version": "1.0.0",
        "database_status": db_status,
        "database_uri_type": "PostgreSQL" if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"] else "SQLite",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": app.config["ENV"]
    }), 200

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"status": "error", "message": "Resource not found", "code": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"status": "error", "message": "Internal server error occurred", "code": 500}), 500

if __name__ == "__main__":
    port = app.config["PORT"]
    print(f"[Market Watcher Backend] Starting API server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])

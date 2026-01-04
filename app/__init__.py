from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
try:
    from flask_cors import CORS
except Exception:
    CORS = None

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config())
    if CORS:
        CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    from app.models.user import User
    from app.models.product import Product
    from app.models.stock import Stock
    from app.models.transaction import Transaction, TransactionItem
    from app.models.cart import Cart, CartItem
    from app.routes import bp
    app.register_blueprint(bp, url_prefix='/api')

    @app.route('/')
    def root_redirect():
        return redirect('/api/')
    return app
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config())
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models
    from app.models.user import User
    from app.models.product import Product
    from app.models.stock import Stock
    from app.models.transaction import Transaction, TransactionItem
    from app.models.cart import Cart, CartItem
    
    # Register blueprint dengan prefix '/api' jika mau
    from app.routes import bp
    app.register_blueprint(bp)  # atau app.register_blueprint(bp, url_prefix='/api')
    
    return app
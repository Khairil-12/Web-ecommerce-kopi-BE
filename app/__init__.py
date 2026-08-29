from flask import Flask, redirect
from dotenv import load_dotenv
import os

load_dotenv()

from app.config import Config
from app.supabase_client import db

try:
    from flask_cors import CORS
except Exception:
    CORS = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config())
    
    os.environ["SUPABASE_URL"] = app.config.get("SUPABASE_URL")
    os.environ["SUPABASE_KEY"] = app.config.get("SUPABASE_KEY")
    
    if CORS:
        CORS(app, resources={r"/*": {"origins": "*"}})
    
    from app.routes import bp
    app.register_blueprint(bp, url_prefix='/api')

    @app.route('/')
    def root_redirect():
        return redirect('/api/')
    return app
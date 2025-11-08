import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
supabase: Optional[Client] = None  # Python 3.9-compatible Optional type

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load environment variables from .env file for local development
    # In production (Vercel), these will be set in the dashboard
    load_dotenv()

    # Determine if in production
    is_production = os.environ.get('VERCEL_ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production'

    # --- Production-Ready Configuration ---
    
    # 1. Secret Key
    secret_key = os.environ.get('SECRET_KEY')
    if is_production and not secret_key:
        raise ValueError("No SECRET_KEY set for production environment")
    app.config['SECRET_KEY'] = secret_key or 'dev-secret-key-should-be-overridden'

    # 2. Database URL
    database_url = os.environ.get('DATABASE_URL')
    if is_production and not database_url:
        raise ValueError("No DATABASE_URL set for production environment")
    # Fallback to local SQLite for development if DATABASE_URL is not set
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(app.instance_path, 'portfolio.db')
    
    # Ensure the instance folder exists for SQLite
    if not database_url:
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 3. Mail Configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Initialize Supabase
    global supabase
    url: str = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        logger.error("Supabase configuration missing. Ensure SUPABASE_URL and SUPABASE_KEY (or NEXT_PUBLIC_* fallbacks) are set in .env")
        supabase = None
    else:
        try:
            supabase = create_client(url, key)
        except Exception:
            logger.exception("Failed to initialize Supabase client. Check URL/KEY values.")
            supabase = None

    # Expose backend mode for templates/debug
    from .supabase_repo import get_backend_mode
    app.config['DATA_BACKEND'] = get_backend_mode()

    # Blueprints must be registered before create_all and user_loader
    from . import routes, auth
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.auth_bp)

    with app.app_context():
        from .models import User
        # Create database tables
        db.create_all()

        # Flask-Login user loader
        @login_manager.user_loader
        def load_user(user_id: str):
            try:
                return User.query.get(int(user_id))
            except Exception:
                return None

    return app

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
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
supabase: Optional[Client] = None  # Python 3.9-compatible Optional type

def create_app():
    app = Flask(__name__)

    # Load environment variables from common locations
    logger = logging.getLogger(__name__)
    possible_envs = [
        Path(__file__).parent / '.env',         # package-level .env
        Path(__file__).parent.parent / '.env',  # repo root .env
    ]
    for p in possible_envs:
        try:
            if p.exists():
                load_dotenv(dotenv_path=p)
                logger.info("Loaded environment from %s", p)
                break
        except Exception:
            logger.exception("Failed loading .env from %s", p)

    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'portfolio.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    # Import mail lazily to avoid circular import at module load
    from .utils import mail
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

    with app.app_context():
        from . import routes, auth
        from .models import User
        app.register_blueprint(routes.bp)
        app.register_blueprint(auth.auth_bp)

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
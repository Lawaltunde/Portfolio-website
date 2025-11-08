import os
from flask import Flask
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import logging
from typing import Union

import routes
import auth
from models import User, login_manager
from utils import mail

# Initialize extensions at the top level
csrf = CSRFProtect()
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def create_app():
    app = Flask(__name__)

    logging.basicConfig(level=logging.INFO)
    logging.info("Starting to create the Flask app.")

    # Configurations
    is_production = os.environ.get('FLASK_ENV') == 'production'
    secret_key = os.environ.get('SECRET_KEY')
    logging.info("Loaded basic environment variables.")

    if is_production and not secret_key:
        logging.error("SECRET_KEY is not set in production.")
        raise ValueError("SECRET_KEY must be set in the environment for production.")

    app.config['SECRET_KEY'] = secret_key or 'a-temporary-dev-secret-key'
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    logging.info("Mail configuration loaded.")

    # Initialize extensions with the app object
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    logging.info("LoginManager initialized.")
    csrf.init_app(app)
    logging.info("CSRFProtect initialized.")
    limiter.init_app(app)
    logging.info("Limiter initialized.")
    mail.init_app(app)
    logging.info("Mail initialized.")

    try:
        from supabase_client import supabase
        app.supabase = supabase
        if supabase:
            logging.info("Supabase client imported and attached to app successfully.")
        else:
            logging.warning("Supabase client is None after import.")
    except Exception as e:
        logging.error(f"Failed to import or attach Supabase client: {e}")
        raise

    # Register blueprints
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.auth_bp)
    logging.info("Blueprints registered.")

    logging.info("Flask app creation complete.")
    return app

if __name__ == "__main__":
    app = create_app()
    # Production-ready: debug mode is explicitly controlled by an environment variable.
    # Defaults to False (production mode).
    is_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=is_debug)
import os
from flask import Flask
from supabase import create_client, Client
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from typing import Union
import logging
from logging.handlers import RotatingFileHandler

from . import routes
from . import auth
from .models import User, login_manager
from .utils import mail

# Initialize extensions at the top level
csrf = CSRFProtect()
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def create_app():
    app = Flask(__name__)

    # Configurations
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise ValueError("SECRET_KEY must be set in the environment.")

    app.config['SECRET_KEY'] = secret_key
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # For development, use an absolute path to a local SQLite database.
        db_path = os.path.join(app.instance_path, 'portfolio.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app object
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    from .supabase_client import supabase
    app.supabase = supabase

    # Register blueprints
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.auth_bp)

    # Import and register error handlers
    from portfolio import errors

    # Logging
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, log to stdout
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        # In development, log to a file
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/portfolio.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Portfolio startup')

    return app

if __name__ == "__main__":
    app = create_app()
    # Production-ready: debug mode is explicitly controlled by an environment variable.
    # Defaults to False (production mode).
    is_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=is_debug)
import os
from flask import Flask
from supabase import create_client, Client
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from dotenv import load_dotenv
from pathlib import Path
import logging
from typing import Union

import routes
import auth
from models import db, User, login_manager

def create_app():
    app = Flask(__name__)

    # Load environment variables
    dotenv_path = Path('./.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Configurations
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
    CSRFProtect(app)
    Limiter(get_remote_address, app=app, storage_uri="memory://")
    Mail(app)

    from supabase_client import supabase
    app.supabase = supabase

    # Register blueprints
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.auth_bp)

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
import os
from flask import Flask, render_template, request, redirect, abort, flash, url_for
from supabase import create_client, Client
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email as _validate_email, EmailNotValidError
import click
import logging
from flask_mail import Mail, Message as MailMessage


from dotenv import load_dotenv
from pathlib import Path

# Instantiating a Flask class
app = Flask(__name__)

# Load environment variables from .env file
dotenv_path = Path('./.env')
load_dotenv(dotenv_path=dotenv_path)

# Initialize Supabase client (legacy path). Prefer factory in __init__.py
url: str = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client | None = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception:
        logging.getLogger(__name__).exception("Failed to initialize Supabase client in app.py")

# Secret key for session management (use environment variable in production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)
db = SQLAlchemy(app)
# Whitelist of templates that can be rendered via the dynamic page route
ALLOWED_TEMPLATES = {
    'about.html': 'about.html',
    'portfolio.html': 'portfolio.html',
    'contact.html': 'contact.html',
    'thank_you.html': 'thank_you.html',
    'error404.html': 'error404.html',
    'login.html': 'login.html',
    'register.html': 'register.html',
    'dashboard.html': 'dashboard.html',
    'index.html': 'index.html',
}

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# CSRF protection
csrf = CSRFProtect(app)

# Logging setup
logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Make csrf_token() available in Jinja templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# CSRF error handler
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return "CSRF token missing or invalid.", 400

# Rate limiting (in-memory). For production, configure a shared backend like Redis.
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")



# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    projects = db.relationship('Project', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    github_url = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    tech_stack = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Flask-Login user loader (must be outside class)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Local-only CLI command to create an admin without exposing an HTTP route
@app.cli.command('create-admin')
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--role', default='admin', help='The role of the user to create.')
def create_admin_cli(username, password, role):
    """Create an admin user via CLI in an atomic way: flask create-admin"""
    user = User(username=username.strip(), role=role)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
        click.echo('Admin user created.')
    except IntegrityError:
        db.session.rollback()
        click.echo('Admin creation failed: username already exists or a concurrent creation occurred.', err=True)
    except Exception as e:
        db.session.rollback()
        click.echo(f'Admin creation failed: {e}', err=True)

@app.route("/")
def hello_world():
    return render_template('index.html')


# Admin login route
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = supabase.auth.sign_in_with_password({
                "email": form.email.data,
                "password": form.password.data
            })
            login_user(user)
            if user.user.user_metadata.get('role') == 'admin':
                return redirect('/admin')
            return redirect('/dashboard')
        except Exception as e:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

# Register route
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = supabase.auth.sign_up({
                "email": form.email.data,
                "password": form.password.data,
            })
            login_user(user)
            return redirect('/dashboard')
        except Exception as e:
            flash('Registration failed: ' + str(e), 'danger')
    return render_template('register.html', form=form)


# Admin logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Admin dashboard (protected)
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    projects = Project.query.all()
    return render_template('dashboard.html', projects=projects, is_admin=True)

# Project dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        github_url = request.form.get('github_url')
        image_url = request.form.get('image_url')
        tech_stack = request.form.get('tech_stack')

        new_project = Project(
            title=title,
            description=description,
            github_url=github_url,
            image_url=image_url,
            tech_stack=tech_stack,
            user_id=current_user.id
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect('/dashboard')

    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', projects=projects)

# Edit project
@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.github_url = request.form.get('github_url')
        project.image_url = request.form.get('image_url')
        project.tech_stack = request.form.get('tech_stack')
        db.session.commit()
        return redirect('/dashboard')

    return render_template('edit_project.html', project=project)

# Delete project
@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        abort(403)
    
    db.session.delete(project)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/user/<username>')
@login_required
def user_page(username):
    if current_user.username != username:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_page.html', user=user)

@app.route("/<string:page_name>")
def html_page(page_name: str):
    template = ALLOWED_TEMPLATES.get(page_name)
    if not template:
        return abort(404)
    return render_template(template)


# Store message in the database
def storing_database(data: dict) -> None:
    """Validate input and store a contact message in the database.

    Raises:
        ValueError: If validation fails for any field.
        RuntimeError: If a database error occurs while saving.
    """
    # Required fields and basic max length constraints aligned with DB schema
    required_fields = {
        'user_name': 100,
        'email': 120,
        'subject': 200,
        'text': None,  # message body (no strict DB length, but must be non-empty)
    }

    # Presence and basic validation
    cleaned = {}
    for field, max_len in required_fields.items():
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        value = str(data.get(field, '')).strip()
        if not value:
            raise ValueError(f"Field '{field}' must not be empty")
        if max_len is not None and len(value) > max_len:
            raise ValueError(f"Field '{field}' exceeds maximum length of {max_len}")
        cleaned[field] = value

    # Robust email validation
    try:
        # Validate format; skip deliverability/MX checks to avoid network calls
        validated = _validate_email(cleaned['email'], check_deliverability=False)
        cleaned['email'] = validated.email  # use normalized form
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email address: {str(e)}")

    # Map 'text' to message body column
    new_message = Message(
        user_name=cleaned['user_name'],
        email=cleaned['email'],
        subject=cleaned['subject'],
        message=cleaned['text'],
    )

    try:
        db.session.add(new_message)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Failed to store contact message: %s", exc)
        raise RuntimeError("Failed to save message. Please try again later.")

def send_email(subject, recipients, template, **kwargs):
    """Send an email notification using a template."""
    msg = MailMessage(subject, recipients=recipients)
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


@app.route("/submited_form", methods=['POST', 'GET'])
def submited_form():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            storing_database(data)
            # Send email notification using the new template
            send_email(
                subject=f"New Inquiry from {data.get('user_name', 'a visitor')}: {data.get('subject', '')}",
                recipients=[os.environ.get('MAIL_DEFAULT_SENDER')],
                template='email_template.html',
                name=data.get('user_name'),
                email=data.get('email'),
                message=data.get('text')
            )
        except ValueError as ve:
            # Client error: bad input
            return str(ve), 400
        except RuntimeError as re:
            # Server error while persisting
            return str(re), 500
        except Exception:
            logger.exception("Unexpected error handling contact form")
            return "Unexpected error", 500
        return redirect('/thank_you.html')
    else:
        return redirect('/error404.html')
    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
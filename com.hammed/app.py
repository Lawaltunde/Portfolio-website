from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
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

load_dotenv()

# Instantiating a Flask class
app = Flask(__name__)

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

# Dummy password hash for constant-time checks when user does not exist
DUMMY_PW_HASH = generate_password_hash(os.environ.get('DUMMY_PASSWORD', 'not-the-real-password'))

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

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

"""
/create_admin: Disabled by default for security.
Enable only temporarily by setting environment variable ENABLE_ADMIN_CREATION=1.
Optionally set ADMIN_CREATION_TOKEN and pass ?token=... to the route for extra gating.
Remove this route in production to avoid race-condition exploits.
"""
@csrf.exempt
@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if os.environ.get('ENABLE_ADMIN_CREATION') not in {'1', 'true', 'TRUE', 'True'}:
        return abort(403)

    token_required = os.environ.get('ADMIN_CREATION_TOKEN')
    if token_required:
        provided = request.args.get('token')
        if not provided or provided != token_required:
            return abort(403)

    if User.query.first():
        return "Admin already exists. Remove or comment out this route for security.", 403

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            return "Username and password required.", 400
        if len(username) < 3:
            return "Username must be at least 3 characters.", 400
        if len(password) < 8:
            return "Password must be at least 8 characters.", 400
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return '''
        <h2>Create Admin User</h2>
        <form method="POST">
            <label>Username:</label><br>
            <input type="text" name="username" required><br>
            <label>Password:</label><br>
            <input type="password" name="password" required><br><br>
            <button type="submit">Create Admin</button>
        </form>
    '''

# Local-only CLI command to create an admin without exposing an HTTP route
@app.cli.command('create-admin')
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin_cli(username, password):
    """Create an admin user via CLI in an atomic way: flask create-admin"""
    user = User(username=username.strip())
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
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        # Constant-time password verification: always check against a hash
        hash_to_check = user.password_hash if user else DUMMY_PW_HASH
        pw_ok = False
        try:
            pw_ok = check_password_hash(hash_to_check, password)
        except Exception:
            # In case of malformed hash or unexpected error, treat as failure
            pw_ok = False

        if pw_ok and user is not None:
            login_user(user)
            return redirect('/admin')
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

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
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template('admin.html', messages=messages)

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
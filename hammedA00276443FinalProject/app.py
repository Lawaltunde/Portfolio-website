import csv
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os


# Instantiating a Flask class
app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
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

# One-time admin creation route (remove after use)
@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if User.query.first():
        return "Admin already exists. Remove or comment out this route for security.", 403
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return "Username and password required.", 400
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

@app.route("/")
def hello_world():
    return render_template('index.html')


# Admin login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/admin')
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Admin logout route
@app.route('/logout')
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
def html_page(page_name):
    return render_template(page_name)


# Store message in the database
def storing_database(data):
    user_name = data['user_name']
    email = data['email']
    subject = data['subject']
    message = data['text']
    new_message = Message(user_name=user_name, email=email, subject=subject, message=message)
    db.session.add(new_message)
    db.session.commit()

@app.route("/submited_form", methods = ['POST', 'GET'])
def submited_form():
    if request.method == 'POST':
        data = request.form.to_dict()
        storing_database(data)
        return redirect('/thank_you.html')
    else:
        return redirect('/error404.html')
    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

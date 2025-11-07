from flask import Blueprint, request, redirect, flash, render_template, session
from flask_login import login_user, logout_user, login_required
from supabase_client import supabase
from models import User
from supabase_repo import get_supabase_context_from_env, get_backend_mode

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Supabase-only login; permit only admins to proceed to the app."""
    if request.method == 'POST':
        try:
            if get_backend_mode() == 'supabase' and supabase is None:
                raise RuntimeError("Supabase is not configured")
            email = request.form.get('email')
            password = request.form.get('password')
            sres = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            try:
                session["supabase_token"] = sres.session.access_token
            except Exception:
                session.pop("supabase_token", None)

            is_admin = False
            try:
                ctx = get_supabase_context_from_env()
                client = ctx.user_client() if ctx else None
                if client is not None:
                    admin_check = client.table('admins').select('user_id').eq('user_id', sres.user.id).single().execute()
                    is_admin = bool(admin_check.data)
            except Exception:
                is_admin = False

            if not is_admin:
                flash('You are not authorized to access admin.', 'danger')
                return render_template('login.html')

            user = User(id=sres.user.id, username=email, role='admin')
            session['user_details'] = {'id': user.id, 'username': user.username, 'role': user.role}
            login_user(user)
            return redirect('/admin')
        except Exception:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    flash('Registration is disabled. Please contact the site owner.', 'warning')
    return redirect('/login')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop("supabase_token", None)
    session.pop('user_details', None)
    logout_user()
    return redirect('/login')
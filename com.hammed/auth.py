import os
from flask import Blueprint, request, redirect, flash, render_template, session
from flask_login import login_user, logout_user, login_required
from supabase_client import supabase
from models import db, User
from supabase_repo import get_supabase_context_from_env, get_backend_mode

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Supabase-only login; permit only admins to proceed to the app."""
    if request.method == 'POST':
        try:
            # In supabase mode, supabase must be configured
            if get_backend_mode() == 'supabase' and supabase is None:
                raise RuntimeError("Supabase is not configured")
            email = request.form.get('email')
            password = request.form.get('password')
            sres = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            # persist the access_token for RLS-aware postgrest calls
            try:
                session["supabase_token"] = sres.session.access_token  # type: ignore[attr-defined]
            except Exception:
                session.pop("supabase_token", None)

            # Check admin membership via RLS using a user-bound client
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

            # Ensure local user exists and marked as admin for Flask-Login
            db_user = User.query.filter_by(username=email).first()
            if not db_user:
                db_user = User(username=email, role='admin')
                # set a dummy password to satisfy NOT NULL; Supabase handles auth
                try:
                    db_user.set_password(os.urandom(16).hex())
                except Exception:
                    # fallback to a static non-sensitive dummy
                    db_user.set_password('supabase-only-login')
                db.session.add(db_user)
                db.session.commit()
            elif db_user.role != 'admin':
                db_user.role = 'admin'
                db.session.commit()

            login_user(db_user)
            return redirect('/admin')
        except Exception:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

# Registration route disabled for now (admin provisioned via Supabase dashboard)
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    flash('Registration is disabled. Please contact the site owner.', 'warning')
    return redirect('/login')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop("supabase_token", None)
    logout_user()
    return redirect('/login')
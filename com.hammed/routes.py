import logging
from flask import Blueprint, render_template, request, redirect, abort, flash, url_for, current_app
from flask_login import login_required, current_user
from flask_limiter import Limiter
from utils import send_email
from flask import session
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from supabase_repo import get_supabase_context_from_env, ProjectRepo, BlogRepo, get_backend_mode

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

ALLOWED_TEMPLATES = {
    'about.html': 'about.html',
    'portfolio.html': 'portfolio.html',
    'contact.html': 'contact.html',
    'thank_you.html': 'thank_you.html',
    'error404.html': 'error404.html',
    'login.html': 'login.html',
    'register.html': 'register.html',
    'index.html': 'index.html',
}

@bp.route("/")
def hello_world():
    return render_template('index.html')

@bp.route('/test')
def test():
    return "Test route is working!"

# Dynamic portfolio page: render projects from DB if available
@bp.route('/portfolio.html')
def portfolio_page():
    ctx = get_supabase_context_from_env()
    projects = []
    if ctx is not None:
        projects = ProjectRepo(ctx).list_projects()
    return render_template('portfolio.html', projects=projects)

# Admin dashboard overview: lists projects and blog posts in tables
@bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    projects = ProjectRepo(ctx).list_projects() if ctx is not None else []
    posts = BlogRepo(ctx).list_posts() if ctx is not None else []
    return render_template('admin_dashboard.html', projects=projects, posts=posts, is_admin=True)

# Projects manager (GET list/form, POST create)
@bp.route('/admin/projects', methods=['GET', 'POST'])
@login_required
def admin_projects():
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        github_url = request.form.get('github_url')
        image_url = request.form.get('image_url')
        tech_stack = request.form.get('tech_stack')

        # Handle optional image file upload
        uploaded = request.files.get('image_file')
        if not session.get('supabase_token'):
            flash('Admin token missing. Please log out and log in again to continue.', 'warning')
            return redirect(url_for('routes.admin_projects'))
        if uploaded and uploaded.filename and ctx is not None:
            filename = secure_filename(uploaded.filename)
            image_public_url = ProjectRepo(ctx).upload_image(
                uploaded.stream.read(), filename, uploaded.mimetype or 'image/jpeg'
            )
            if image_public_url:
                image_url = image_public_url
        if ctx is not None:
            created = ProjectRepo(ctx).create_project(
                title=title,
                description=description,
                github_url=github_url,
                image_url=image_url,
                tech_stack=tech_stack,
            )
            if created is None:
                flash('Failed to create project in Supabase', 'danger')
        else:
            flash('Supabase is not configured; cannot create project in supabase mode.', 'danger')
        return redirect(url_for('routes.admin_projects'))

    projects = ProjectRepo(ctx).list_projects() if ctx is not None else []
    return render_template('admin_projects.html', projects=projects, is_admin=True)

# Back-compat: keep /dashboard but redirect to the new projects manager
@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)
    return redirect(url_for('routes.admin_projects'))

# Edit project
@bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    if request.method == 'POST':
        fields = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'github_url': request.form.get('github_url'),
            'image_url': request.form.get('image_url'),
            'tech_stack': request.form.get('tech_stack'),
        }
        if ctx is not None:
            ok = ProjectRepo(ctx).update_project(project_id, fields)
            if not ok:
                flash('Failed to update project in Supabase', 'danger')
        else:
            flash('Supabase is not configured; cannot update project in supabase mode.', 'danger')
        # Optional redirect back to provided 'next'
        next_url = request.args.get('next') or request.form.get('next')
        if next_url and isinstance(next_url, str) and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('routes.admin_projects'))

    # GET
    project = ProjectRepo(ctx).get_project(project_id) if ctx is not None else None
    if not project:
        abort(404)
    return render_template('edit_project.html', project=project)

# Delete project
@bp.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    if ctx is not None:
        ok = ProjectRepo(ctx).delete_project(project_id)
        if not ok:
            flash('Failed to delete project in Supabase', 'danger')
    else:
        flash('Supabase is not configured; cannot delete project in supabase mode.', 'danger')
    return redirect(url_for('routes.admin_projects'))

@bp.route("/<string:page_name>")
def html_page(page_name: str):
    template = ALLOWED_TEMPLATES.get(page_name)
    if not template:
        return abort(404)
    if template == 'portfolio.html':
        return portfolio_page()
    return render_template(template)

@bp.route("/submited_form", methods=['POST', 'GET'])
def submited_form():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            # Send email notification using the new template
            send_email(
                subject=f"New Inquiry from {data.get('user_name', 'a visitor')}: {data.get('subject', '')}",
                recipients=[os.environ.get('MAIL_DEFAULT_SENDER')],
                template='email_template.html',
                name=data.get('user_name'),
                email=data.get('email'),
                message=data.get('text')
            )
        except Exception:
            logging.exception("An error occurred while sending the email.")
            return "Unexpected error", 500
        return redirect('/thank_you.html')
    else:
        return redirect('/error404.html')

# Public blog listing
@bp.route('/blogs')
def blogs():
    ctx = get_supabase_context_from_env()
    posts = BlogRepo(ctx).list_posts() if ctx is not None else []
    return render_template('blogs.html', posts=posts)

# Public blog detail
@bp.route('/blogs/<int:post_id>')
def blog_detail(post_id: int):
    ctx = get_supabase_context_from_env()
    post = BlogRepo(ctx).get_post(post_id) if ctx is not None else None
    if not post:
        abort(404)
    return render_template('blog_detail.html', post=post)

# Admin: blogs manager (GET list/form, POST create)
@bp.route('/admin/blogs', methods=['GET', 'POST'])
@login_required
def admin_blogs():
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('Title and content are required', 'danger')
            return redirect(url_for('routes.admin_blogs'))
        if not session.get('supabase_token'):
            flash('Admin token missing. Please log out and log in again to continue.', 'warning')
            return redirect(url_for('routes.admin_blogs'))
        if ctx is not None:
            ok = BlogRepo(ctx).create_post(title.strip(), content.strip()) is not None
            if not ok:
                flash('Failed to create blog post in Supabase', 'danger')
        else:
            flash('Supabase is not configured; cannot create blog post in supabase mode.', 'danger')
        flash('Blog post created', 'success')
        return redirect(url_for('routes.admin_blogs'))

    posts = BlogRepo(ctx).list_posts() if ctx is not None else []
    return render_template('admin_blogs.html', posts=posts, is_admin=True)

# Admin: delete blog post
@bp.route('/admin/blogs/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_blog(post_id: int):
    if current_user.role != 'admin':
        abort(403)
    ctx = get_supabase_context_from_env()
    if ctx is not None:
        ok = BlogRepo(ctx).delete_post(post_id)
        if not ok:
            flash('Failed to delete blog post in Supabase', 'danger')
    else:
        flash('Supabase is not configured; cannot delete blog post in supabase mode.', 'danger')
    flash('Blog post deleted', 'success')
    next_url = request.args.get('next') or request.form.get('next')
    if next_url and isinstance(next_url, str) and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('routes.admin_blogs'))
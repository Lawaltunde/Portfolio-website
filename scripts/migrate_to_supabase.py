import os
from typing import Optional

from flask import Flask

from . import create_app, db
from .models import Project, BlogPost
from .supabase_repo import get_supabase_context_from_env


def main() -> int:
    app: Flask = create_app()
    ctx = get_supabase_context_from_env()
    if ctx is None:
        print("Supabase env not configured. Set SUPABASE_URL and SUPABASE_KEY.")
        return 2
    admin = ctx.admin_client()
    if admin is None:
        print("SUPABASE_SERVICE_ROLE_KEY is required for migration.")
        return 2

    with app.app_context():
        # migrate projects
        projects = Project.query.order_by(Project.id.asc()).all()
        print(f"Migrating {len(projects)} projects...")
        for p in projects:
            payload = {
                "title": p.title,
                "description": p.description,
                "github_url": p.github_url,
                "image_url": p.image_url,
                "tech_stack": p.tech_stack,
            }
            try:
                admin.table("projects").upsert(payload, on_conflict="title").execute()
            except Exception as e:
                print("Failed project:", p.id, e)

        # migrate blog posts
        posts = BlogPost.query.order_by(BlogPost.id.asc()).all()
        print(f"Migrating {len(posts)} blog posts...")
        for b in posts:
            payload = {
                "title": b.title,
                "content": b.content,
            }
            try:
                admin.table("blog_posts").upsert(payload, on_conflict="title").execute()
            except Exception as e:
                print("Failed blog:", b.id, e)

    print("Migration completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

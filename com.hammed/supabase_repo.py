import os
import io
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from flask import session
from supabase import create_client, Client


class SupabaseContext:
    """
    Provides per-request Supabase clients:
    - user_client: uses the end-user access token (RLS-enforced)
    - admin_client: uses the service role for maintenance/migrations only
    """

    def __init__(self, url: str, anon_key: str, service_role_key: Optional[str] = None):
        self.url = url
        self.anon_key = anon_key
        self.service_role_key = service_role_key

    def user_client(self) -> Optional[Client]:
        token = session.get("supabase_token")
        if not token:
            return None
        client = create_client(self.url, self.anon_key)
        # Attach user's bearer token for RLS
        client.postgrest.auth(token)
        return client

    def admin_client(self) -> Optional[Client]:
        if not self.service_role_key:
            return None
        return create_client(self.url, self.service_role_key)

    def anon_client(self) -> Optional[Client]:
        if not self.url or not self.anon_key:
            return None
        # anon client without bearer, RLS evaluates as role=anon
        return create_client(self.url, self.anon_key)


class ProjectRepo:
    def __init__(self, ctx: SupabaseContext, bucket: str = "portfolio"):
        self.ctx = ctx
        self.bucket = bucket

    # ---------- Storage helpers ----------
    def upload_image(self, file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Uploads an image to Supabase Storage under the configured bucket.
        Returns a public URL on success, else None.
        """
        client = self.ctx.user_client()
        if client is None:
            return None
        # Unique key per upload to avoid collisions
        key = f"uploads/{uuid.uuid4().hex}_{filename}"
        try:
            client.storage.from_(self.bucket).upload(
                file=file_bytes,
                path=key,
                file_options={"contentType": content_type, "upsert": False},
            )
            public = client.storage.from_(self.bucket).get_public_url(key)
            return public
        except Exception:
            return None

    # ---------- Projects (table: projects) ----------
    def list_projects(self) -> List[Dict[str, Any]]:
        client = self.ctx.user_client() or self.ctx.anon_client() or self.ctx.admin_client()
        if client is None:
            return []
        try:
            resp = (
                client.table("projects").select("*").order("id", desc=True).execute()
            )
            return resp.data or []
        except Exception:
            return []

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        client = self.ctx.user_client() or self.ctx.anon_client() or self.ctx.admin_client()
        if client is None:
            return None
        try:
            resp = client.table("projects").select("*").eq("id", project_id).single().execute()
            return resp.data
        except Exception:
            return None

    def create_project(
        self,
        title: str,
        description: str,
        github_url: Optional[str],
        image_url: Optional[str],
        tech_stack: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        client = self.ctx.user_client()
        if client is None:
            return None
        payload = {
            "title": title,
            "description": description,
            "github_url": github_url,
            "image_url": image_url,
            "tech_stack": tech_stack,
        }
        try:
            resp = client.table("projects").insert(payload).select("*").single().execute()
            return resp.data
        except Exception:
            return None

    def update_project(
        self,
        project_id: int,
        fields: Dict[str, Any],
    ) -> bool:
        client = self.ctx.user_client()
        if client is None:
            return False
        try:
            client.table("projects").update(fields).eq("id", project_id).execute()
            return True
        except Exception:
            return False

    def delete_project(self, project_id: int) -> bool:
        client = self.ctx.user_client()
        if client is None:
            return False
        try:
            client.table("projects").delete().eq("id", project_id).execute()
            return True
        except Exception:
            return False


class BlogRepo:
    def __init__(self, ctx: SupabaseContext):
        self.ctx = ctx

    def list_posts(self) -> List[Dict[str, Any]]:
        client = self.ctx.user_client() or self.ctx.anon_client() or self.ctx.admin_client()
        if client is None:
            return []
        try:
            resp = client.table("blog_posts").select("*").order("created_at", desc=True).execute()
            return resp.data or []
        except Exception:
            return []

    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        client = self.ctx.user_client() or self.ctx.anon_client() or self.ctx.admin_client()
        if client is None:
            return None
        try:
            resp = client.table("blog_posts").select("*").eq("id", post_id).single().execute()
            return resp.data
        except Exception:
            return None

    def create_post(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        client = self.ctx.user_client()
        if client is None:
            return None
        payload = {"title": title, "content": content}
        try:
            resp = client.table("blog_posts").insert(payload).select("*").single().execute()
            return resp.data
        except Exception:
            return None

    def delete_post(self, post_id: int) -> bool:
        client = self.ctx.user_client()
        if client is None:
            return False
        try:
            client.table("blog_posts").delete().eq("id", post_id).execute()
            return True
        except Exception:
            return False


def get_supabase_context_from_env() -> Optional[SupabaseContext]:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    anon = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    service = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not anon:
        return None
    return SupabaseContext(url, anon, service)


def get_backend_mode() -> str:
    """Return the selected data backend: 'supabase' or 'sqlite'.

    Precedence:
    - DATA_BACKEND env var if explicitly set to 'supabase' or 'sqlite'.
    - Otherwise, auto-detect: if Supabase URL+KEY are present -> 'supabase', else 'sqlite'.
    """
    val = (os.environ.get("DATA_BACKEND") or "").strip().lower()
    if val in ("supabase", "sqlite"):
        return val
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    anon = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    return "supabase" if (url and anon) else "sqlite"

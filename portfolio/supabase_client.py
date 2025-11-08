import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

from pathlib import Path
from typing import Union, Optional
import logging

url: Optional[str] = os.environ.get("SUPABASE_URL")
key: Optional[str] = os.environ.get("SUPABASE_KEY")
supabase: Union[Client, None] = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception:
        logging.getLogger(__name__).exception("Failed to initialize Supabase client")
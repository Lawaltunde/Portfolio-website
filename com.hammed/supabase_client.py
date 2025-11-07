import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Union
import logging

# Load environment variables
dotenv_path = Path('./.env')
load_dotenv(dotenv_path=dotenv_path)

# Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Union[Client, None] = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception:
        logging.getLogger(__name__).exception("Failed to initialize Supabase client")
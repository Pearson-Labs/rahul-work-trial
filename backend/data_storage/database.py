import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create supabase client directly - simple approach
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
        print("⚠️  Supabase credentials not found - database features will be limited")
except Exception as e:
    supabase = None
    print(f"⚠️  Supabase connection failed: {e}")

def get_supabase_client():
    """Get Supabase client - fallback function for compatibility"""
    if supabase is None:
        raise ValueError("Supabase URL and Key must be set in environment variables")
    return supabase

# The following functions are for reference and manual execution in Supabase SQL Editor.
# Programmatic DDL execution with supabase-py is not directly supported


if __name__ == "__main__":
    print("Supabase client initialized. Please run the SQL script below manually in your Supabase SQL Editor:")

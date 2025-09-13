import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# The following functions are for reference and manual execution in Supabase SQL Editor.
# Programmatic DDL execution with supabase-py is not directly supported


if __name__ == "__main__":
    print("Supabase client initialized. Please run the SQL script below manually in your Supabase SQL Editor:")

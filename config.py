import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

# Centralized environment variables
class Config:
    ENV = os.getenv("APP_ENV", "staging")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL = os.getenv("DATABASE_URL")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLIC_KEY = os.getenv("SUPABASE_PUBLIC_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")


    # Function to validate required env vars
    @classmethod
    def validate(cls):
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "SUPABASE_URL",
            "SUPABASE_PUBLIC_KEY",
            "SUPABASE_SERVICE_KEY",
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError("Missing required variables")

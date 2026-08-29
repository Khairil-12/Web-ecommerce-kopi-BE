import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = str(os.environ.get("SECRET_KEY", "secret-key"))
    SUPABASE_URL = str(os.environ.get("SUPABASE_URL"))
    SUPABASE_KEY = str(os.environ.get("SUPABASE_KEY"))
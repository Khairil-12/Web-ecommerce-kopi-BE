import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    HOST = str(os.environ.get("DB_HOST", "localhost"))
    DATABASE = str(os.environ.get("DB_DATABASE", "ecommerce_kopi"))
    USERNAME = str(os.environ.get("DB_USERNAME", "root"))
    PASSWORD = str(os.environ.get("DB_PASSWORD", ""))
    SECRET_KEY = str(os.environ.get("SECRET_KEY", "secret-key"))
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
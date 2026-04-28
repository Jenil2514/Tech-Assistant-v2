import psycopg2
from app.config.settings import settings

def get_db():
    return psycopg2.connect(settings.DB_URL)
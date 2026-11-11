import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, dotenv_values

def get_db_connection():
    load_dotenv()
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor,
    )
def get_db_cursor(connection):
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        return cursor
    except Exception as e:
        print(f"Error creating a database cursor: {e}")
        raise

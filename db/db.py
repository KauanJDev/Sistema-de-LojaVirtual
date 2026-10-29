import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "seubanco"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        cursor_factory=RealDictCursor,
    )

def get_db_cursor(connection):
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        return cursor
    except Exception as e:
        print(f"Error creating a database cursor: {e}")
        raise
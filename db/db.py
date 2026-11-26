import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

env_path = str(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(env_path)

url = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
)
engine = create_engine(url, pool_pre_ping=True)
Sessao = sessionmaker(engine)

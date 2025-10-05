import os
from  dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DB_HOSTNAME = os.getenv("TAQWA_TRACKER_DB_HOSTNAME")
DB_NAME = os.getenv("TAQWA_TRACKER_DB_NAME")
DB_USERNAME = os.getenv("TAQWA_TRACKER_DB_USERNAME")
DB_PASSWORD = os.getenv("TAQWA_TRACKER_DB_PASSWORD")
DB_PORT = os.getenv("TAQWA_TRACKER_DB_PORT")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
if not DB_HOSTNAME or not DB_NAME or not DB_USERNAME or not DB_PASSWORD or not DB_PORT:
    raise ValueError("Database configuration environment variables are not set properly.")

engine = create_engine(DATABASE_URL)

def get_db_session():
    with Session(engine, autocommit=False, autoflush=False) as session:
        yield session

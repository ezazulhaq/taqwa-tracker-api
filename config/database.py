import os
from  dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DB_HOSTNAME = os.getenv("TAQWA_TRACKER_DB_HOSTNAME")
DB_NAME = os.getenv("TAQWA_TRACKER_DB_NAME")
DB_USERNAME = os.getenv("TAQWA_TRACKER_DB_USERNAME")
DB_PASSWORD = os.getenv("TAQWA_TRACKER_DB_PASSWORD")
DB_PORT = os.getenv("TAQWA_TRACKER_DB_PORT")

if not DB_HOSTNAME or not DB_NAME or not DB_USERNAME or not DB_PASSWORD or not DB_PORT:
    missing_vars = []
    if not DB_HOSTNAME: missing_vars.append("TAQWA_TRACKER_DB_HOSTNAME")
    if not DB_NAME: missing_vars.append("TAQWA_TRACKER_DB_NAME")
    if not DB_USERNAME: missing_vars.append("TAQWA_TRACKER_DB_USERNAME")
    if not DB_PASSWORD: missing_vars.append("TAQWA_TRACKER_DB_PASSWORD")
    if not DB_PORT: missing_vars.append("TAQWA_TRACKER_DB_PORT")
    raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def get_db_session():
    with Session(engine, autocommit=False, autoflush=False) as session:
        yield session

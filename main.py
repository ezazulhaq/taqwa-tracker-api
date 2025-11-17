import tomllib
from pathlib import Path
from fastapi import FastAPI
from routers import admin, auth, chat, feedback, library, quran, status, user

# Read version from pyproject.toml
with open(Path(__file__).parent / "pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)
    version = pyproject["project"]["version"]

app = FastAPI(
    title="Taqwa Tracker API",
    version=version,
    docs_url="/api/documentation",
    redoc_url="/api/re-documentation",
    openapi_url="/api/openapi.json"
)

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(quran.router)
app.include_router(library.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(feedback.router)
app.include_router(admin.router)

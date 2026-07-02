import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from src.auth.routes import auth_router

from contextlib import asynccontextmanager
from src.db.main import initdb, get_session
from src.pki.pki_engine import ensure_root_ca_exists
from src.pki.routes import pki_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import text
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-vue", "dist")


async def database_ping():
    """Test database connection and get current time from DB"""
    try:
        async for session in get_session():
            result = await session.execute(text(
                "SELECT NOW() as current_time, "
                "version() as db_version"
            ))
            db_info = result.first()
            current_db_time = db_info.current_time
            db_version = db_info.db_version.split(',')[0]
            print(f"🗓️  DATABASE PING SUCCESSFUL")
            print(f"   📍 Source: PostgreSQL Database")
            print(f"   🕐 Database Time: {current_db_time}")
            print(f"   🏷️  Database Version: {db_version}")
            print(f"   💻 Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🔗 Connection: Active")
            await session.close()
            return True
    except Exception as e:
        print(f"❌ DATABASE PING FAILED")
        print(f"   📍 Source: PostgreSQL Database")
        print(f"   💥 Error: {e}")
        print(f"   💻 Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 Connection: Failed")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initdb()
    print("🔍 Testing database connection...")
    db_connected = await database_ping()
    if db_connected:
        print("✅ Database connection verified - Application starting")
    else:
        print("🚨 Database connection failed - Check your configuration")

    # Ensure the Root CA (our automated passport office) exists before
    # the app starts accepting requests.
    ensure_root_ca_exists()

    yield
    print("🛑 Server is stopping")


app = FastAPI(
    title="USR",
    version="v1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes must be registered BEFORE any static file mounts
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    pki_router,
    prefix="/api/certificates",
    tags=["certificates"],
)

try:
    from src.auth.routes import auth_router as _ar  # noqa: F811
    print("✅ Auth router imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")

# ── Static file serving from the built Vue app ────────────────────────────
# Serve assets (JS/CSS/images) from the Vite dist folder.
# The assets sub-path is mounted first so FastAPI serves them directly.
app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(DIST_DIR, "assets")),
    name="assets",
)

# SPA catch-all: any path that isn't an /auth/* API route or an /assets/*
# static file should return index.html so Vue Router can handle navigation.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    index = os.path.join(DIST_DIR, "index.html")
    return FileResponse(index)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from sqlmodel import text, SQLModel
from src.config import Config
from sqlalchemy.orm import sessionmaker
import os
# IMPORTANT!
# Even if you don't use the classes directly in that file,
# importing it ensures the metadata includes it.
from src.auth.models import User
from src.pki.models import ClientCertificate  # noqa: F401 — registers table in metadata

def get_async_db_url(url: str) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// for async driver"""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Strip ?ssl query param - handled via connect_args
    if "?ssl" in url:
        url = url.split("?ssl")[0]
    return url

db_url = get_async_db_url(Config.DATABASE_URL)

# Determine if SSL is needed (not needed for Replit's internal helium DB)
_is_internal = "helium" in Config.DATABASE_URL or os.getenv("PGHOST", "") == "helium"

if _is_internal:
    connect_args = {}
else:
    import ssl
    ssl_context = ssl.create_default_context()
    connect_args = {"ssl": ssl_context}

engine = create_async_engine(
    url=db_url,
    echo=True,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

async def initdb():
    async with engine.begin() as conn:
        from src.auth.models import User
        from src.pki.models import ClientCertificate  # noqa: F401 — ensure table registered
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Database tables created/verified successfully.")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from sqlmodel import text, SQLModel
from src.config import Config
import ssl
from sqlalchemy.orm import sessionmaker
# IMPORTANT!
# Even if you don’t use the classes directly in that file, 
# importing it ensures the metadata includes it.
from src.auth.models import User

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    url=Config.DATABASE_URL, # no ?sslmode=require&?channelbinding=require here in dburl
    echo=True,
    # asyncpg expects an actual ssl.SSLContext object, 
    # not a string like ?sslmode=require in the dburl path in the .env file.
    connect_args={"ssl": ssl_context},
    # the following 2 resolve a session management issue 
    pool_pre_ping=True,  # ✅ - checks connection before use
    pool_recycle=300,    # ✅ - recycles connections every 5 minutes
)
"""
async def initdb():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Database tables created successfully.")
"""

async def initdb():
    async with engine.begin() as conn:
        # IMPORTANT!
        # importing it ensures the metadata includes it.
        from src.auth.models import User

        ### Drop all tables (only in dev!)
        ## Important Note Below: 
        # Model has been updated with 2 # 2FA Fields
        # 1. is_2fa_enabled and
        # 2. totp_secret
        # this has to be run as well at least the first time
        # outside dev mode

        ######################
        ######################
        await conn.run_sync(SQLModel.metadata.drop_all)

        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

        # cemment out when not dropping tables
        print("Dropped and recreated all tables.")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    # async_sessionmaker creates a factory for instantiating sessions
    async_session = async_sessionmaker(
        bind = engine,
        class_ = AsyncSession,
        expire_on_commit = False,
        # suggested to improve session management
        autoflush=False,  # ✅ FOR better control
    )

    # PREV implementation - open a new session context
    # async with async_session() as session:
    #     yield session
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()  # ✅ Ensure session is properly closed    
    
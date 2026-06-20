import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from src.auth.routes import auth_router

# the lifespan function will be decorated with asynccontextmanager 
# from the contextlib module in Python.
from contextlib import asynccontextmanager
from src.db.main import initdb, get_session
# import psycopg2

# serve frontend from fast api
# add static file serving
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# the following ping the db
from sqlmodel import text
from datetime import datetime
import asyncio

# For debugging purposes, pinging the db precedes the lifespan event declaration
async def database_ping():
    """Test database connection and get current time from DB"""
    try:
        async for session in get_session():
            result = await session.execute(text(
                "SELECT NOW() as current_time, " \
                "version() as db_version"
                ))
            db_info = result.first()
            
            current_db_time = db_info.current_time
            # get just the PostgreSQL version
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

# This function is a lifespan event because it runs once before the application starts 
# and then continues throughout the application's lifespan.
@asynccontextmanager
async def lifespan(app: FastAPI):    
    #print("Server is starting...")
    # instead of a regular print, we can  establish a connection to the database and 
    # execute a SELECT statement, which will return the string "Hello World" 
    # as demonstrated in the provided output.
    await initdb()

    # adding db ping to db lifespan event for testing purposes
    # comment out as necessary
    ## Test database connection with ping
    print("🔍 Testing database connection...")
    db_connected = await database_ping()
    if db_connected:
        print("✅ Database connection verified - Application starting")
    else:
        print("🚨 Database connection failed - Check your configuration")

    yield
    print("🛑 Server is stopping")


app = FastAPI(
    title="USR",
    version = "v1",
    lifespan=lifespan # add the lifespan event to our application
)


# Added CORS middleware
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],  # to be adjusted
    ## note: can actually stay ["*"], seeing as how the -curl tests worked 
    ## on full 2fa implementation from backend only 

    # allow_credentials=True with allow_origins=["*"] - Firefox blocks this combination for security!
     # !!!!!!!!! SPECIFYING EXPLICIT ORIGINS !!!!!!!!!
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(
    auth_router,
    prefix="/auth",
    tags=['auth']
)


# Serving static files for everything else AFTER including auth router
# API routes must come 
# BEFORE static file mounts because FastAPI matches routes \
# in the order they're defined

# Serve static files from frontend folder
# Serve static files (frontend), only once
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
# Frontend is on the same origin - http://localhost:8000
# So the CORS issue shouldn't be the problem since 
# frontend and backend are on same origin (no cross-origin requests).



# Removing (commenting out) the duplicate route 
# - the mount above handles the root
# @app.get("/")
# async def serve_frontend():
#     return FileResponse('frontend/index.html')

#@app.get("/{full_path:path}")
#async def catch_all(full_path: str):
#    # Serve the frontend for any other route (for client-side routing)
#    return FileResponse('frontend/index.html')

# previous implementation before static serving
# @app.get("/")
# async def root():
#    return {"message": "USR Authentication Service"}

# for debugging purposes
# to be commented out later on
try:
    from src.auth.routes import auth_router
    print("✅ Auth router imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    # Create a simple router for testing
    from fastapi import APIRouter
    auth_router = APIRouter()
    
    @auth_router.post("/signup")
    async def test_signup():
        return {"message": "Test endpoint working"}


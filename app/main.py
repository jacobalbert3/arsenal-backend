# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.routers import projects, learnings, favorites, auth, rag
from app.middleware.security import SecurityHeadersMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

# Create the FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()

# Set up rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#WHY CORS? -> allow frontend to make requests to backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(https:\/\/(www\.)?arsenal-dev\.com|http:\/\/localhost:\d+|vscode-webview:\/\/[^/]+)$", #allow production, local, and vscode-webview
    allow_credentials=True, #allows sending auth tokens and cookies 
    allow_methods=["*"], #allows all methods
    allow_headers=["*"], #allows all headers
    expose_headers=["*"] #allows all headers to be exposed
)

# Security headsers for (XSS, clickjacking, etc)
app.add_middleware(SecurityHeadersMiddleware)



#run this function when the app starts
@app.on_event("startup")
async def startup():
    await database.connect()

#run this function when the app shuts down
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Connect the /projects routes
app.include_router(projects.router)
app.include_router(learnings.router)
app.include_router(favorites.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(rag.router)

@app.get("/health")
async def health_check():
    try:
        # Check database connection
        await database.fetch_one("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.routers import projects, learnings, favorites, auth, rag
from app.middleware.security import SecurityHeadersMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI()

load_dotenv()

# Add security headers middleware BEFORE CORS
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
#app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# CORS middlewarewa
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://arsenal-azure.vercel.app",
#         "https://arsenal-os2t98dib-jacobalbert3s-projects.vercel.app",
#         "http://localhost:3000",
#         "vscode-webview://*"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
async def startup():
    await database.connect()

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

port = int(os.getenv("PORT", 8000))

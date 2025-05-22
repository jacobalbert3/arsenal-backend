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
from app.middleware.ssl import SSLMiddleware

app = FastAPI()

load_dotenv()


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(https:\/\/(www\.)?arsenal-dev\.com|http:\/\/localhost:\d+|vscode-webview:\/\/.*?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add security headers middleware BEFORE CORS
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
#app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Add SSL middleware if production
# if os.getenv("NODE_ENV") == "production":
#     app.add_middleware(SSLMiddleware)

app.add_middleware(SSLMiddleware)
# CORS middlewarewa



# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://www.arsenal-dev.com",
#         "https://arsenal-dev.com",
#         "http://localhost:3000",
#     ],
#     allow_origin_regex=r"^vscode-webview://.*$",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=r"^(vscode-webview://.*|https://.*arsenal.*|http://localhost:3000)$",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )


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

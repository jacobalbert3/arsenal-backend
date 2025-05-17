# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.routers import projects, learnings, favorites, auth, rag
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

# 👇 Allow requests from your Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://arsenal-azure.vercel.app",
        "https://arsenal-os2t98dib-jacobalbert3s-projects.vercel.app",
        "http://localhost:3000"  # Keep this for local development
    ],
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

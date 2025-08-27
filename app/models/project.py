# app/models/project.py
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from app.models import metadata
from app.db import database


projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("github_repo", String, nullable=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
)
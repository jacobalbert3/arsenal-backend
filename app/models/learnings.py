# app/models/learning.py

from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey
from pgvector.sqlalchemy import Vector
from app.models import metadata  # shared!
from app.db import database

learnings = Table(
    "learnings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("file_path", String, nullable=False),
    Column("function_name", String, nullable=True),
    Column("library_name", String, nullable=True),
    Column("description", Text, nullable=False),
    Column("code_snippet", Text, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("embedding", Vector(1536), nullable=True),
)

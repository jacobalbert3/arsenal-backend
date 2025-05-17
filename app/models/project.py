# app/models/project.py

from sqlalchemy import Table, Column, Integer, String
from app.models import metadata  # shared!
from app.db import database


projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("github_repo", String, nullable=True),
    Column("user_id", Integer, nullable=False),
)

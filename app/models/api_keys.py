from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from app.models import metadata
from datetime import datetime


api_keys = Table(
    "api_keys",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("token", String, unique=True, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("project_id", Integer, ForeignKey("projects.id"), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False)
)


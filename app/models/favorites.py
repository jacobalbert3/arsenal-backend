# app/models/favorites.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.models import metadata

favorites = Table(
    "favorites",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("learning_id", Integer, ForeignKey("learnings.id", ondelete="CASCADE")),
)
# app/models/usage_limits.py
from sqlalchemy import Table, Column, Integer, String, UniqueConstraint, MetaData, ForeignKey
from app.models import metadata  # shared!

usage_limits = Table(
    "usage_limits",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("month_key", String, nullable=False),
    Column("powered_queries_count", Integer, default=0),
    UniqueConstraint('user_id', 'month_key', name='unique_user_month')
)
# app/models/users.py
import sqlalchemy
from app.models import metadata


users = sqlalchemy.Table(
    "users",
    metadata, #enables creation when you call metadata.create_all
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),  # hashed
)
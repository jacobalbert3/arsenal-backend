import os
from sqlalchemy import create_engine, text, Index
from app.models import metadata
from app.models.project import projects
from app.models.learnings import learnings
from app.models.favorites import favorites
from app.models.users import users
from app.models.api_keys import api_keys
from app.models.usage_limits import usage_limits
from urllib.parse import urlparse

def initialize_db():
    ENV = os.getenv("ENV", "local")

    if ENV == "production":
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise RuntimeError("❌ DATABASE_URL not set for production")
        # Add SSL mode for Railway
        url = urlparse(DATABASE_URL)
        DATABASE_URL = f"{url.scheme}://{url.netloc}{url.path}?sslmode=require"
    else:
        DATABASE_URL = "postgresql://postgres@localhost/arsenal_db"

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"🔧 Initializing DB in {ENV} mode...")

    # Enable pgvector
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("✅ pgvector extension enabled.")

    # WARNING: Only drop tables in local!
    if ENV != "production":
        print("⚠️ Dropping and recreating tables (local only)...")
        metadata.drop_all(engine)
        metadata.create_all(engine)
    else:
        print("✅ Skipping drop/create in production.")

    # Create indexes
    Index('idx_api_keys_token', api_keys.c.token, unique=True).create(bind=engine)
    Index('idx_api_keys_user_project', api_keys.c.user_id, api_keys.c.project_id).create(bind=engine)
    Index('idx_learnings_project', learnings.c.project_id).create(bind=engine)
    Index('idx_learnings_user', learnings.c.user_id).create(bind=engine)
    Index('idx_favorites_user', favorites.c.user_id).create(bind=engine)
    Index('idx_projects_user', projects.c.user_id).create(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_learnings_embedding
            ON learnings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))

    print("🎉 Arsenal DB initialized.")

# 🔹 Only run if executed directly
if __name__ == "__main__":
    initialize_db()

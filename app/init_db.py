from sqlalchemy import create_engine, text, Index
from app.db import database
from app.models import metadata
from app.models.project import projects
from app.models.learnings import learnings
from app.models.favorites import favorites
from app.models.users import users
from app.models.api_keys import api_keys
from app.models.usage_limits import usage_limits
import getpass

# Automatically use your actual macOS user for Postgres
DATABASE_URL = f"postgresql://{getpass.getuser()}@localhost/arsenal_db"
engine = create_engine(DATABASE_URL)

# ✅ 1. Enable pgvector BEFORE table creation
with engine.begin() as conn:  # 🚨 MUST be engine.begin() not connect()
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("✅ pgvector extension enabled.")
    except Exception as e:
        print("❌ Failed to create pgvector extension.")
        raise e

# ✅ 2. Drop and recreate all tables
metadata.drop_all(engine)
metadata.create_all(engine)
print("✅ Tables created.")

# ✅ 3. Create indexes AFTER tables exist
Index('idx_api_keys_token', api_keys.c.token, unique=True).create(bind=engine)
Index('idx_api_keys_user_project', api_keys.c.user_id, api_keys.c.project_id).create(bind=engine)
Index('idx_learnings_project', learnings.c.project_id).create(bind=engine)
Index('idx_learnings_user', learnings.c.user_id).create(bind=engine)
Index('idx_favorites_user', favorites.c.user_id).create(bind=engine)
Index('idx_projects_user', projects.c.user_id).create(bind=engine)
print("✅ Standard indexes created.")

# ✅ 4. Now create the vector index on learnings table
with engine.connect() as conn:
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_learnings_embedding
        ON learnings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """))
print("✅ Vector index created.")

print("✅ Arsenal DB initialized.")

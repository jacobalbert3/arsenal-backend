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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def initialize_db():
    PUBLIC_DATABASE_URL = os.getenv("PUBLIC_DATABASE_URL")
    
    if not PUBLIC_DATABASE_URL:
        print("❌ PUBLIC_DATABASE_URL not set in environment")
        return

    print(f"🔌 Connecting to: {PUBLIC_DATABASE_URL}")
    
    url = urlparse(PUBLIC_DATABASE_URL)
    DATABASE_URL = f"{url.scheme}://{url.netloc}{url.path}?sslmode=require"
    
    print("🔧 Creating engine...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    try:
        print("🔍 Testing connection...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Connection successful!")

        # Enable pgvector
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("✅ pgvector extension enabled.")

        # WARNING: Only drop tables in local!
        
        print("✅ Creating tables if they don't exist...")
        metadata.create_all(engine)

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
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise

# 🔹 Only run if executed directly
if __name__ == "__main__":
    initialize_db()

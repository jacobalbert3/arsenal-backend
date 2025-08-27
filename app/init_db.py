#Used to reset the db. NOTE: will delete existing data.
import os
from sqlalchemy import create_engine, text, Index
from app.models import metadata
from app.models.project import projects
from app.models.learnings import learnings
from app.models.favorites import favorites
from app.models.users import users
from app.models.api_keys import api_keys
from app.models.usage_limits import usage_limits

from dotenv import load_dotenv

#INSTRUCTIONS TO REMOVE THE DATABASE
#railway login; railway link; railway shell; railway run python -m app.init_db

#connect via CLI: railway link; psql $DATABASE_URL


#used to get current user (for local db / testing...)
import getpass

# Load env stuff
load_dotenv()

def initialize_db():   
    #set by railway -> same as the one from pgvector
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = f"postgresql://{getpass.getuser()}@localhost/arsenal_db"
    else:
        # Convert postgres:// to postgresql:// to make sure it is in the form for sqlalchemy
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')



    #pool = collection of ready-to-use database connections
    #when app needs to run query, grabs connection from the pool

    # Create engine with SSL required for Railway
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True, #checks if connection is still alive before using it
        pool_size=5, #keep up to 5 connections open
        max_overflow=10, #allow extra 10 
        connect_args={
            "connect_timeout": 30 #wait 30 seconds when trying to connect 
        }
    )

    try:
        #connect to the pool 
        with engine.connect() as conn:
            #run simple query to make sure works:
            conn.execute(text("SELECT 1"))

        # Enable pgvector
        #with = context manager -> ensures connection is closed after use
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("pgvector extension working.")

        # Drop existing indexes first
        with engine.begin() as conn:
            conn.execute(text("DROP INDEX IF EXISTS idx_learnings_embedding;"))
            conn.execute(text("DROP INDEX IF EXISTS idx_api_keys_token;"))
            conn.execute(text("DROP INDEX IF EXISTS idx_learnings_project;"))
            conn.execute(text("DROP INDEX IF EXISTS idx_learnings_user;"))
            conn.execute(text("DROP INDEX IF EXISTS idx_favorites_user;"))
            conn.execute(text("DROP INDEX IF EXISTS idx_projects_user;"))

        print("dropping existing tables")
        metadata.drop_all(engine)
        metadata.create_all(engine)
        print("Tables created successfully!")

        # Rationale behind index choices...

        # IMPORTANT -> every API request will use token index
        Index('idx_api_keys_token', api_keys.c.token, unique=True).create(bind=engine)
        # Helpful for joins (get_learning_by_library, )
        Index('idx_learnings_project', learnings.c.project_id).create(bind=engine)
        #learnings by user: high frequency on dashboard and for RAG queries
        Index('idx_learnings_user', learnings.c.user_id).create(bind=engine)
        #get favorites at high frequency
        Index('idx_favorites_user', favorites.c.user_id).create(bind=engine)
        #used whenever view dashboard and and want projects for a user (also used in project ownership verification)
        Index('idx_projects_user', projects.c.user_id).create(bind=engine)

        #create vector index for similarity search
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_learnings_embedding
                ON learnings
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """))

        print("Database init complete")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_db()

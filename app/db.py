# app/db.py

import os
from databases import Database
from urllib.parse import urlparse

# Get DATABASE_URL from Railway or fallback to local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/arsenal_db")

# Handle Railway's PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Parse URL but don't force SSL
if "localhost" not in DATABASE_URL:
    url = urlparse(DATABASE_URL)
    #removes query params that might cause issues
    DATABASE_URL = f"{url.scheme}://{url.netloc}{url.path}"

# Create the database connection
database = Database(DATABASE_URL)

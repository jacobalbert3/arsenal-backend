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

async def ensure_connected():
    """Simple function to check if connected and reconnect if needed"""
    if not database.is_connected:
        await database.connect()

async def execute_with_reconnect(operation, *args, **kwargs):
    """Execute database operation with automatic reconnection if needed"""
    try:
        # Make sure we're connected
        await ensure_connected()
        
        # Execute the operation
        if hasattr(operation, '__call__'):
            result = await operation(*args, **kwargs)
        else:
            result = operation(*args, **kwargs)
        
        return result
        
    except Exception as e:
        # If operation failed, try to reconnect and retry once
        try:
            await database.disconnect()
            await database.connect()
            
            # Try the operation again
            if hasattr(operation, '__call__'):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            return result
            
        except Exception as retry_error:
            # If retry also failed, raise the original error
            raise e

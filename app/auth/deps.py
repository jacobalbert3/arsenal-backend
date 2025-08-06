from fastapi import Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from app.db import database
from app.models.api_keys import api_keys
from sqlalchemy import select, join
from app.models.users import users
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_user_from_api_key(api_key: str) -> int:
    """Validate an API key and return user info"""
    # Update the query syntax to SQLAlchemy 2.0 style
    query = select(users.c.id).select_from(
        join(api_keys, users, api_keys.c.user_id == users.c.id)
    ).where(api_keys.c.token == api_key)
    
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result['id']

async def get_current_user_id(
    authorization: str = Header(None)
) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = authorization.split()
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    auth_type, token = parts

    if auth_type.lower() == "bearer":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return int(user_id)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    elif auth_type.lower() == "apikey":
        return await get_user_from_api_key(token)
    
    
    raise HTTPException(status_code=401, detail="Invalid authorization type")

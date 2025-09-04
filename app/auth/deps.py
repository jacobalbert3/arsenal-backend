from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt
import os
from app.db import database, execute_with_reconnect
from app.models.api_keys import api_keys
from sqlalchemy import select, join
from app.models.users import users
from dotenv import load_dotenv

#GOAL: get the user_id from the auth token or api key

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
#algorithm used to sign the JWT
ALGORITHM = "HS256"


async def get_user_from_api_key(api_key: str) -> int:
    #join API keys and users to find all user ids with that api key
    query = select(users.c.id).select_from(
        join(api_keys, users, api_keys.c.user_id == users.c.id)
    ).where(api_keys.c.token == api_key)
    
    try:
        # Use the simple reconnection wrapper
        result = await execute_with_reconnect(
            database.fetch_one, 
            query
        )
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return result['id']
        
    except Exception as e:
        # If it's an auth error, re-raise it
        if "Invalid API key" in str(e):
            raise e
        # Otherwise, it's a connection error
        raise HTTPException(status_code=500, detail="Database connection error")

async def get_current_user_id(
    #gets the authorization header from the HTTP request
    authorization: str = Header(None)
) -> int:
    #if no authorization header, throw error
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    #split the authorization header into two parts: auth_type and token
    parts = authorization.split()
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    #get the auth type and token
    auth_type, token = parts
    #if the auth type is bearer, decode the token
    if auth_type.lower() == "bearer":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            #gets the user_id from the token
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            #return the user_id
            return int(user_id)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    #if the auth type is apikey, get the user_id from the api key
    elif auth_type.lower() == "apikey":
        return await get_user_from_api_key(token)
    
    
    raise HTTPException(status_code=401, detail="Invalid authorization type")

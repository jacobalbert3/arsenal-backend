from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from passlib.hash import bcrypt
from app.db import database
from app.models.users import users
from app.models.api_keys import api_keys
from app.models.project import projects
from app.auth.jwt import create_access_token
from app.auth.deps import get_current_user_id
from sqlalchemy import select, insert, delete, join
#for generating api keys
import secrets
import string
from datetime import datetime, timedelta

# Import the global limiter
from app.limiter import limiter

router = APIRouter()

# Add this model for login request validation
class LoginRequest(BaseModel):
    email: str
    password: str

# Add request model for API key generation
class ApiKeyRequest(BaseModel):
    project_id: int

@router.post("/signup")
@limiter.limit("5/minute")  # Prevent rapid account creation
async def signup(request: Request, data: dict):
    try:
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Email and password required",
                    "type": "validation_error"
                }
            )
        #check if user already exists
        existing = await database.fetch_one(users.select().where(users.c.email == email))
        if existing:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "User already exists",
                    "type": "duplicate_user",
                    "field": "email"
                }
            )

        hashed_password = bcrypt.hash(password)
        query = users.insert().values(email=email, password=hashed_password)
        user_id = await database.execute(query)
        #create access token for user
        access_token = create_access_token({"sub": str(user_id)})
        
        return {
            "message": "User created",
            "user_id": user_id,
            "access_token": access_token
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": str(e),
                "type": "server_error"
            }
        )


@router.post("/login")
async def login(request: LoginRequest):
    user = await database.fetch_one(
        users.select().where(users.c.email == request.email)
    )
    #check if user exists and password is correct
    if not user or not bcrypt.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    #create access token for user
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }

def generate_api_key() -> str:
    """Generate a secure API key with prefix"""
    return f"ak_{secrets.token_hex(32)}"

#GENERATE API KEY FOR A PROJECT:
@router.post("/generate-key")
@limiter.limit("5/minute")  # Prevent rapid API key generation
async def generate_api_key_route(
    request: Request,
    data: ApiKeyRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        # Verify project ownership
        project_check = await database.fetch_one(
            select(projects).where(projects.c.id == data.project_id).where(projects.c.user_id == current_user_id)
        )
        
        if not project_check:
            raise HTTPException(status_code=403, detail="Project not found or not owned by you")
        
        # Delete existing API key if it exists for THAT project
        await database.execute(
            delete(api_keys).where(api_keys.c.user_id == current_user_id).where(api_keys.c.project_id == data.project_id)
        )
        
        # Generate and insert new API key
        api_key = generate_api_key()
        query = insert(api_keys).values(
            token=api_key,
            user_id=current_user_id,
            project_id=data.project_id,
            created_at=datetime.utcnow()
        )
        
        await database.execute(query)
        return {"api_key": api_key}
    except Exception as e:
        print(f"Error generating API key: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Could not generate API key: {str(e)}"
        )

#
async def validate_api_key(authorization: str = Header(...)) -> dict:
    """Validate an API key and return user and project info"""
    if not authorization.startswith("ApiKey "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header. Must start with 'ApiKey '"
        )
    
    api_key = authorization.replace("ApiKey ", "")
    
    query = select(
        users.c.id.label("user_id"),
        users.c.email,
        api_keys.c.project_id
    ).select_from(
        join(api_keys, users, api_keys.c.user_id == users.c.id)
    ).where(api_keys.c.token == api_key)
    
    result = await database.fetch_one(query)
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return {
        "user_id": result["user_id"],
        "email": result["email"],
        "project_id": result["project_id"]
    }

# Example protected route using API key authentication
@router.get("/test-api-key")
async def test_api_key(user: dict = Depends(validate_api_key)):
    return {"message": "API key is valid", "user": user}


from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from passlib.hash import bcrypt
from app.db import database
from app.models.users import users
from app.models.api_keys import api_keys
from app.auth.jwt import create_access_token
from app.auth.deps import get_current_user_id
import secrets
import string
from datetime import datetime, timedelta

router = APIRouter()

# Add this model for login request validation
class LoginRequest(BaseModel):
    email: str
    password: str

# Add request model for API key generation
class ApiKeyRequest(BaseModel):
    project_id: int

@router.post("/signup")
async def signup(data: dict):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    existing = await database.fetch_one(users.select().where(users.c.email == email))
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = bcrypt.hash(password)

    query = users.insert().values(email=email, password=hashed_password)
    user_id = await database.execute(query)
    
    # Create access token after signup
    access_token = create_access_token({"sub": str(user_id)})
    
    return {
        "message": "User created",
        "user_id": user_id,
        "access_token": access_token
    }


@router.post("/login")
async def login(request: LoginRequest):
    user = await database.fetch_one(
        users.select().where(users.c.email == request.email)
    )
    if not user or not bcrypt.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
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

@router.post("/generate-key")
async def generate_api_key_route(
    request: ApiKeyRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        # Verify project ownership
        project_check = await database.fetch_one(
            "SELECT id FROM projects WHERE id = :project_id AND user_id = :user_id",
            values={"project_id": request.project_id, "user_id": current_user_id}
        )
        
        if not project_check:
            raise HTTPException(status_code=403, detail="Project not found or not owned by you")
        
        # Delete existing API key if it exists
        await database.execute(
            "DELETE FROM api_keys WHERE user_id = :user_id AND project_id = :project_id",
            values={"user_id": current_user_id, "project_id": request.project_id}
        )
        
        # Generate and insert new API key
        api_key = generate_api_key()
        query = api_keys.insert().values(
            token=api_key,
            user_id=current_user_id,
            project_id=request.project_id,
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

async def validate_api_key(authorization: str = Header(...)) -> dict:
    """Validate an API key and return user and project info"""
    if not authorization.startswith("ApiKey "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header. Must start with 'ApiKey '"
        )
    
    api_key = authorization.replace("ApiKey ", "")
    
    query = """
        SELECT u.id as user_id, u.email, ak.project_id
        FROM api_keys ak 
        JOIN users u ON u.id = ak.user_id 
        WHERE ak.token = :token
    """
    
    result = await database.fetch_one(
        query=query,
        values={"token": api_key}
    )
    
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


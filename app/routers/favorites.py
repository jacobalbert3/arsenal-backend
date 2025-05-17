from fastapi import APIRouter, HTTPException, Query, Depends
from app.db import database
from app.models.favorites import favorites
from sqlalchemy import select, insert, delete
from app.auth.deps import get_current_user_id

router = APIRouter()

@router.post("/users/{user_id}/favorites")
async def add_favorite(
    user_id: int,
    data: dict,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    learning_id = data.get("learning_id")
    if not learning_id:
        raise HTTPException(status_code=400, detail="Missing learning_id")

    query = insert(favorites).values(user_id=current_user_id, learning_id=learning_id)
    await database.execute(query)
    return {"message": "Added to favorites"}

@router.delete("/users/{user_id}/favorites")
async def remove_favorite(
    user_id: int,
    learning_id: int = Query(...),
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = delete(favorites).where(
        favorites.c.user_id == current_user_id,
        favorites.c.learning_id == learning_id
    )
    await database.execute(query)
    return {"message": "Removed from favorites"}

@router.get("/users/{user_id}/favorites")
async def get_favorites(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    join_query = """
    SELECT l.*, f.learning_id
    FROM favorites f
    JOIN learnings l ON f.learning_id = l.id
    WHERE f.user_id = :user_id
    """
    rows = await database.fetch_all(query=join_query, values={"user_id": current_user_id})
    return rows
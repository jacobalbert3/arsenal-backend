from fastapi import APIRouter, HTTPException, Query, Depends
from app.db import database
from app.models.favorites import favorites
from app.models.learnings import learnings
from sqlalchemy import select, insert, delete, join
from app.auth.deps import get_current_user_id

router = APIRouter()

#ADD A LEARNING TO FAVORITES:
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

#REMOVE A LEARNING FROM FAVORITES:
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

#GET ALL FAVORITES FOR A USER:
@router.get("/users/{user_id}/favorites")
async def get_favorites(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

   # Convert to match the rest of your codebase
    j = join(favorites, learnings, favorites.c.learning_id == learnings.c.id)
    query = (
        select(
            learnings.c.id,
            learnings.c.file_path,
            learnings.c.function_name,
            learnings.c.library_name,
            learnings.c.description,
            learnings.c.code_snippet,
            favorites.c.learning_id
        )
        .select_from(j)
        .where(favorites.c.user_id == current_user_id)
    )
    rows = await database.fetch_all(query)
    return rows
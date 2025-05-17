from fastapi import APIRouter, HTTPException, Request, Depends
from app.db import database
from app.models.learnings import learnings
from app.models.project import projects
from sqlalchemy import select, join, update, delete
from app.auth.deps import get_current_user_id

router = APIRouter()

@router.get("/projects/{project_id}/learnings")
async def get_learnings(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # First verify project ownership
    project = await database.fetch_one(
        select(projects).where(
            projects.c.id == project_id,
            projects.c.user_id == current_user_id
        )
    )
    if not project:
        raise HTTPException(status_code=403, detail="Project not found or not owned by you")

    query = select(learnings).where(learnings.c.project_id == project_id)
    results = await database.fetch_all(query)
    
    # Format results similar to other endpoints
    formatted_learnings = []
    for row in results:
        learning = {
            "id": row["id"],
            "file_path": row["file_path"],
            "function_name": row["function_name"],
            "library_name": row["library_name"],
            "description": row["description"],
            "code_snippet": row["code_snippet"],
            "project_id": row["project_id"],
            "user_id": row["user_id"]
        }
        formatted_learnings.append(learning)
    
    return formatted_learnings

@router.get("/users/{user_id}/learnings/library/{library_name}")
async def get_learnings_by_library(
    user_id: int,
    library_name: str,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    j = join(learnings, projects, learnings.c.project_id == projects.c.id)
    query = (
        select(
            projects.c.name.label("project_name"),
            learnings.c.id,
            learnings.c.file_path,
            learnings.c.function_name,
            learnings.c.library_name,
            learnings.c.description,
            learnings.c.code_snippet
        )
        .select_from(j)
        .where(
            projects.c.user_id == current_user_id,
            learnings.c.library_name == library_name
        )
    )
    rows = await database.fetch_all(query)

    # Group by project_name logic remains the same
    grouped = {}
    for row in rows:
        project = row["project_name"]
        learning = {
            "id": row["id"],
            "file_path": row["file_path"],
            "function_name": row["function_name"],
            "library_name": row["library_name"],
            "description": row["description"],
            "code_snippet": row["code_snippet"]
        }
        grouped.setdefault(project, []).append(learning)

    return [
        {"project_name": name, "learnings": grouped[name]}
        for name in grouped
    ]

@router.get("/users/{user_id}/learnings/function/{function_name}")
async def get_learnings_by_function(
    user_id: int,
    function_name: str,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    j = join(learnings, projects, learnings.c.project_id == projects.c.id)
    query = (
        select(
            projects.c.name.label("project_name"),
            learnings.c.id,
            learnings.c.file_path,
            learnings.c.function_name,
            learnings.c.library_name,
            learnings.c.description,
            learnings.c.code_snippet
        )
        .select_from(j)
        .where(
            projects.c.user_id == current_user_id,
            learnings.c.function_name == function_name
        )
    )
    rows = await database.fetch_all(query)

    # Group by project_name
    grouped = {}
    for row in rows:
        project = row["project_name"]
        learning = {
            "id": row["id"],
            "file_path": row["file_path"],
            "function_name": row["function_name"],
            "library_name": row["library_name"],
            "description": row["description"],
            "code_snippet": row["code_snippet"]
        }
        grouped.setdefault(project, []).append(learning)

    return [
        {"project_name": name, "learnings": grouped[name]}
        for name in grouped
    ]

@router.put("/learnings/{learning_id}")
async def update_learning(
    learning_id: int,
    request: Request,
    current_user_id: int = Depends(get_current_user_id)
):
    # First verify learning ownership through project
    learning = await database.fetch_one(
        select([learnings, projects.c.user_id])
        .select_from(
            join(learnings, projects, learnings.c.project_id == projects.c.id)
        )
        .where(learnings.c.id == learning_id)
    )
    
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    
    if learning['user_id'] != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this learning")

    payload = await request.json()
    values = {k: v for k, v in payload.items() if v is not None}

    if not values:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    query = update(learnings).where(learnings.c.id == learning_id).values(**values)
    await database.execute(query)
    return {"message": "Learning updated successfully"}

@router.delete("/learnings/{learning_id}")
async def delete_learning(
    learning_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # First verify learning ownership through project
    learning = await database.fetch_one(
        select(learnings, projects.c.user_id)
        .select_from(
            join(learnings, projects, learnings.c.project_id == projects.c.id)
        )
        .where(learnings.c.id == learning_id)
    )
    
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    
    if learning['user_id'] != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this learning")

    query = delete(learnings).where(learnings.c.id == learning_id)
    await database.execute(query)
    return {"message": "Learning deleted successfully"}

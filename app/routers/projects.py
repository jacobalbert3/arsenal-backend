from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, distinct, join
from app.db import database
from app.models.project import projects
from app.models.learnings import learnings
from app.auth.deps import get_current_user_id
from fastapi import Depends
from typing import Optional

router = APIRouter()

# Pydantic models
class ProjectIn(BaseModel):
    name: str
    github_repo: Optional[str] = None

class LearningIn(BaseModel):
    file_path: str
    function_name: Optional[str] = None
    library_name: Optional[str] = None
    description: str
    code_snippet: str


#check that the person owns the project they want to write to
@router.get("/projects/{project_id}")
async def check_project_ownership(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    project = await database.fetch_one(
        select(projects).where(projects.c.id == project_id, projects.c.user_id == current_user_id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by you")
    return {"message": "Project is valid and owned by you"}

@router.get("/users/{user_id}/projects")
async def list_projects(user_id: int, current_user_id: int = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = select(projects).where(projects.c.user_id == user_id)
    results = await database.fetch_all(query)
    return results

# ✅ Create a project for a user
@router.post("/users/{user_id}/projects")
async def create_project(
    user_id: int,
    project: ProjectIn,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = projects.insert().values(
        name=project.name,
        github_repo=project.github_repo,
        user_id=user_id
    )
    project_id = await database.execute(query)
    return {"id": project_id, "message": "Project created"}

# ✅ Create a learning for a project (include user_id)
@router.post("/projects/{project_id}/learnings")
async def create_learning(
    project_id: int,
    learning: LearningIn,
    current_user_id: int = Depends(get_current_user_id)
):
    project_check = await database.fetch_one(
        select(projects).where(projects.c.id == project_id, projects.c.user_id == current_user_id)
    )          
    if not project_check:
        raise HTTPException(status_code=403, detail="You don't own this project")
    
    # Convert absolute path to relative path
    file_path = learning.file_path
    if file_path.startswith('/'):
        # Remove leading slash
        file_path = file_path[1:]
    
    # Remove any potential Windows-style absolute paths
    if ':' in file_path:  # e.g., C:/Users/...
        file_path = '/'.join(file_path.split('/')[1:])
    
    query = learnings.insert().values(
        project_id=project_id,
        file_path=file_path,  # Store the relative path
        function_name=learning.function_name,
        library_name=learning.library_name,
        description=learning.description,
        code_snippet=learning.code_snippet,
        user_id=current_user_id
    )
    learning_id = await database.execute(query)
    return {"id": learning_id, "message": "Learning logged!"}



# (No change) Get libraries used by a user
@router.get("/users/{user_id}/libraries")
async def get_libraries_for_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    j = join(learnings, projects, learnings.c.project_id == projects.c.id)
    query = select(distinct(learnings.c.library_name)).select_from(j).where(projects.c.user_id == user_id)
    results = await database.fetch_all(query)
    return [row[0] for row in results if row[0] is not None]

# (No change) Get functions used by a user
@router.get("/users/{user_id}/functions")
async def get_functions_for_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    j = join(learnings, projects, learnings.c.project_id == projects.c.id)
    query = select(distinct(learnings.c.function_name)).select_from(j).where(projects.c.user_id == user_id)
    results = await database.fetch_all(query)
    return [row[0] for row in results if row[0] is not None]

#get all learnings for a user
@router.get("/users/{user_id}/learnings")
async def get_all_learnings_for_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        query = select(learnings).where(learnings.c.user_id == user_id)
        results = await database.fetch_all(query)
        
        # Properly format results by explicitly creating dictionaries
        formatted_learnings = []
        for row in results:
            learning = {
                 "id": row["id"],
                "file_path": row["file_path"],
                "function_name": row["function_name"],
                "library_name": row["library_name"],
                "description": row["description"],
                "code_snippet": row["code_snippet"]
            }
            formatted_learnings.append(learning)
        
        return formatted_learnings
    except Exception as e:
        print(f"Error fetching learnings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching learnings: {str(e)}"
        )
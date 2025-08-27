from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel # creates data validation schemas
from sqlalchemy import select, distinct, join # database operations
from app.db import database #async databse connection object 
from app.models.project import projects
from app.models.learnings import learnings
#returns the user id associated with the token
from app.auth.deps import get_current_user_id
#for type hinting
from typing import Optional
from app.services.embedder import embed #embeds text into a vector
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

#what data is expected for project
class ProjectIn(BaseModel):
    name: str
    github_repo: Optional[str] = None

#expected for learning data
class LearningIn(BaseModel):
    file_path: str
    function_name: Optional[str] = None
    library_name: Optional[str] = None
    description: str
    code_snippet: str


#LIST ALL PROJECTS FOR A USER: used in dashboard:
@router.get("/users/{user_id}/projects")
async def list_projects(user_id: int, current_user_id: int = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = select(projects).where(projects.c.user_id == user_id)
    results = await database.fetch_all(query)
    return results

#GET PROJECT BY ID: used by CLI to verify project ownership
@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # Check if project exists and is owned by current user
    project = await database.fetch_one(
        select(projects).where(projects.c.id == project_id, projects.c.user_id == current_user_id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not owned by you")
    return project

#CREATE PROJECT FOR USER
@router.post("/users/{user_id}/projects")
async def create_project(
    user_id: int,
    project: ProjectIn, #validation
    current_user_id: int = Depends(get_current_user_id)
):
    #check if the user is the one creating the project
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    #insert the project into the database
    query = projects.insert().values(
        name=project.name,
        github_repo=project.github_repo,
        user_id=user_id
    )
    project_id = await database.execute(query)
    return {"id": project_id, "message": "Project created"}
#CREATE A LEARNING: used in cli, 
@router.post("/projects/{project_id}/learnings")
async def create_learning(
    project_id: int,
    learning: LearningIn,
    current_user_id: int = Depends(get_current_user_id)
):
    #make sure user signed in is the one who owns the project
    project_check = await database.fetch_one(
        select(projects).where(projects.c.id == project_id, projects.c.user_id == current_user_id)
    )          
    if not project_check:
        raise HTTPException(status_code=403, detail="You don't own this project ://///")
    
    # Convert absolute path to relative path
    file_path = learning.file_path
    if file_path.startswith('/'):
        # Remove leading slash
        file_path = file_path[1:]
    
    # Remove any potential Windows-style absolute paths
    if ':' in file_path:
        file_path = '/'.join(file_path.split('/')[1:])
    
    # Generate embedding using both description and code
    full_text = f"{learning.description}\n\n{learning.code_snippet}"
    try:
        vector = await embed(full_text)
    except Exception as e:
        logger.error(f"Failed to embed learning: {e}")
        raise HTTPException(status_code=500, detail="Embedding failed")

    # Insert learning with embedding (embedding in the learning schema)
    query = learnings.insert().values(
        project_id=project_id,
        file_path=file_path,
        function_name=learning.function_name,
        library_name=learning.library_name,
        description=learning.description,
        code_snippet=learning.code_snippet,
        user_id=current_user_id,
        embedding=vector
    )
    learning_id = await database.execute(query)
    return {"id": learning_id, "message": "Learning logged!"}



#GET ALL LIBRARIES USED BY A USER:
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

#GET ALL FUNCTIONS USED BY A USER:
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

#GET ALL LEARNINGS FOR A USER: (used in extension)
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
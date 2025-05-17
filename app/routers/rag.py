from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from app.auth.deps import get_current_user_id
from app.services.embedder import embed
from app.services.llm import call_gpt4_llm
from app.db import database
import logging
from datetime import datetime
from app.models.usage_limits import usage_limits

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

router = APIRouter()

class Message(BaseModel):
    content: str
    is_user: bool

class QueryRequest(BaseModel):
    query: str
    mode: str = "simple"  # or "powered"
    conversation_history: list[Message] = []

    # Add validator for query length
    @validator('query')
    def validate_query_length(cls, v):
        if len(v) > 500:
            raise ValueError("Query length cannot exceed 500 characters")
        return v

# Add this constant at the top
MONTHLY_QUERY_LIMIT = 100 # Adjust as needed

# Add this helper function
async def check_and_update_usage(user_id: int, database) -> bool:
    # Get current month in YYYY-MM format
    current_month_key = datetime.utcnow().strftime("%Y-%m")
    
    # Try to get existing usage record
    query = """
    SELECT powered_queries_count 
    FROM usage_limits 
    WHERE user_id = :user_id AND month_key = :month_key
    """
    
    result = await database.fetch_one(query, {
        "user_id": user_id,
        "month_key": current_month_key
    })
    
    if not result:
        # Create new month record if doesn't exist
        query = """
        INSERT INTO usage_limits (user_id, month_key, powered_queries_count)
        VALUES (:user_id, :month_key, 1)
        RETURNING powered_queries_count
        """
        await database.execute(query, {
            "user_id": user_id,
            "month_key": current_month_key
        })
        return True
    
    if result['powered_queries_count'] >= MONTHLY_QUERY_LIMIT:
        return False
        
    # Update usage count
    query = """
    UPDATE usage_limits 
    SET powered_queries_count = powered_queries_count + 1
    WHERE user_id = :user_id AND month_key = :month_key
    """
    await database.execute(query, {
        "user_id": user_id,
        "month_key": current_month_key
    })
    
    return True

# Optional: Add a function to get current usage
async def get_current_usage(user_id: int, database) -> dict:
    current_month_key = datetime.utcnow().strftime("%Y-%m")
    
    query = """
    SELECT powered_queries_count 
    FROM usage_limits 
    WHERE user_id = :user_id AND month_key = :month_key
    """
    
    result = await database.fetch_one(query, {
        "user_id": user_id,
        "month_key": current_month_key
    })
    
    return {
        "current_usage": result['powered_queries_count'] if result else 0,
        "limit": MONTHLY_QUERY_LIMIT,
        "month": current_month_key
    }

@router.post("/rag/query")
async def query_rag(request: QueryRequest, current_user_id: int = Depends(get_current_user_id)):
    if request.mode == "powered":
        # Check rate limit for powered mode
        can_make_request = await check_and_update_usage(current_user_id, database)
        if not can_make_request:
            usage = await get_current_usage(current_user_id, database)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Monthly query limit reached",
                    "limit": MONTHLY_QUERY_LIMIT,
                    "current_usage": usage["current_usage"],
                    "month": usage["month"]
                }
            )
    
    # Input validation
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # Get embeddings for the query
    try:
        query_vector = embed(request.query)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

    vector_str = f"'[{','.join(map(str, query_vector))}]'"

    # Retrieve top 5 most similar learnings
    sql = f"""
    SELECT id, description, code_snippet, function_name, library_name,
           embedding <-> {vector_str}::vector as similarity
    FROM learnings
    WHERE user_id = :user_id
    ORDER BY similarity
    LIMIT 3
    """
    rows = await database.fetch_all(sql, {"user_id": current_user_id})
    
    # Add detailed logging
    logger.info(f"Query: {request.query}")
    logger.info(f"Similarity scores: {[{'description': r['description'], 'similarity': r['similarity']} for r in rows]}")

    if request.mode == "simple":
        # Filter for high similarity results
        relevant_results = [r for r in rows if r['similarity'] < 1.4]
        
        if not relevant_results:
            return []  # Return empty array instead of error message
            
        # Format results in a more readable way
        formatted_results = []
        for r in relevant_results:
            result = {
                "title": r['description'],
                "details": [],
                "code_snippet": r['code_snippet']
            }
            
            # Add function and library info if they exist
            if r['function_name']:
                result["details"].append(f"🔧 Function: {r['function_name']}")
            if r['library_name']:
                result["details"].append(f"📚 Library: {r['library_name']}")
            # Add similarity score with better normalization
            result["details"].append(f"✨ Match: {max(0, min(100, (1 - r['similarity']/2) * 100)):.0f}%")
            
            formatted_results.append(result)
            
        return formatted_results

    # Powered mode with conversation history
    relevant_results = [r for r in rows if r['similarity'] < 1.4]
    
    # Format conversation history for the prompt
    conversation_context = "\n".join([
        f"{'User' if msg.is_user else 'Assistant'}: {msg.content}"
        for msg in request.conversation_history
    ])
    
    # Create context from relevant learnings
    learnings_context = "\n\n".join([
        f"Snippet {i+1}:\nDescription: {r['description']}\nCode:\n{r['code_snippet']}"
        for i, r in enumerate(relevant_results)
    ])

    try:
        final_prompt = f"""You are a coding assistant focused on helping users understand and work with their code. You have access to their previous conversations and some of their code learnings.

        Previous conversation:
        {conversation_context}

        Relevant code learnings that might help answer the question:
        {learnings_context}

        Current question: {request.query}

        Instructions:
        1. Answer the question directly and concisely.
        2. When referencing code learnings, use the following format:
           [CODE_LEARNING]
           Title: <learning title>
           Description: <learning description>
           Code:
           ```
           <code snippet>
           ```
           [/CODE_LEARNING]
        3. If none of the code learnings are relevant to the question, don't mention them at all.
        4. If the question is a follow-up, maintain context from the previous conversation.
        5. If you reference a code learning, explain why it's relevant to the question.
        6. Stay focused on programming-related topics.

        Answer:"""
        
        response = await call_gpt4_llm(final_prompt)
        return {"response": response}
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )
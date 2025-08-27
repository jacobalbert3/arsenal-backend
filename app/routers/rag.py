from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from app.auth.deps import get_current_user_id
from app.services.embedder import embed
from app.services.llm import call_gpt4_llm
from app.db import database
import logging
from datetime import datetime
from app.models.usage_limits import usage_limits
from sqlalchemy import select, insert, update, text, delete
import traceback

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the global limiter
from app.limiter import limiter

router = APIRouter()

class Message(BaseModel):
    content: str
    is_user: bool

class QueryRequest(BaseModel):
    query: str #contains the user's query
    mode: str = "simple"  # or "powered"
    conversation_history: list[Message] = [] #contains the conversation history
    
    #RUNS when the user submits a query
    @validator('query')
    def validate_query_length(cls, v):
        if len(v) > 500:
            raise ValueError("Query length cannot exceed 500 characters")
        return v

MONTHLY_QUERY_LIMIT = 300

#CHECKS IF THE USER HAS REACHED THE MONTHLY QUERY LIMIT
async def check_and_update_usage(user_id: int, database) -> bool:
    current_month_key = datetime.utcnow().strftime("%Y-%m")
    query = select(usage_limits).where(
        usage_limits.c.user_id == user_id,
        usage_limits.c.month_key == current_month_key
    )
    result = await database.fetch_one(query)

    if not result:
        # Clean up old records only when creating new month record
        await database.execute(
            delete(usage_limits).where(
                usage_limits.c.month_key != current_month_key,
                usage_limits.c.user_id == user_id
            )
        )
        
        query = insert(usage_limits).values(
            user_id=user_id,
            month_key=current_month_key,
            powered_queries_count=1
        )
        await database.execute(query)
        return True

    if result['powered_queries_count'] >= MONTHLY_QUERY_LIMIT:
        return False

    query = update(usage_limits).where(
        usage_limits.c.user_id == user_id,
        usage_limits.c.month_key == current_month_key
    ).values(
        powered_queries_count=usage_limits.c.powered_queries_count + 1
    )
    await database.execute(query)

    return True

#USED TO MAKE SURE THE USER CAN MAKE ANOTHER REQUEST
async def get_current_usage(user_id: int, database) -> dict:
    current_month_key = datetime.utcnow().strftime("%Y-%m")
    query = select(usage_limits).where(
        usage_limits.c.user_id == user_id,
        usage_limits.c.month_key == current_month_key
    )
    result = await database.fetch_one(query)

    return {
        "current_usage": result['powered_queries_count'] if result else 0,
        "limit": MONTHLY_QUERY_LIMIT,
        "month": current_month_key
    }

#RAG QUERY ENDPOINT
@router.post("/rag/query")
async def query_rag(request: QueryRequest, current_user_id: int = Depends(get_current_user_id)):
    logger.info(f"=== RAG QUERY START ===")
    logger.info(f"User ID: {current_user_id}")
    logger.info(f"Query: {request.query}")
    logger.info(f"Mode: {request.mode}")
    logger.info(f"Conversation history length: {len(request.conversation_history)}")

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
    #QUERY CANNOT BE EMPTY
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info("About to generate embedding...")
    try:
        query_vector = await embed(request.query)
        logger.info(f"Embedding generated successfully, length: {len(query_vector)}")
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to process query")

    #FORMAT THE QUERY VECTOR
    vector_str = f"'[{','.join(map(str, query_vector))}]'"
    logger.info("About to execute database query...")

    #finds the cosine similarity between the query vector and the learnings vector
    sql = f"""
    SELECT id, description, code_snippet, function_name, library_name,
           embedding <-> {vector_str}::vector as similarity
    FROM learnings
    WHERE user_id = :user_id
    ORDER BY similarity
    LIMIT 3
    """
    try:
        rows = await database.fetch_all(sql, {"user_id": current_user_id})
        logger.info(f"Database query successful, found {len(rows)} results")
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Database query failed")

    logger.info(f"Query: {request.query}")
    logger.info(f"Raw similarity scores: {[{'description': r['description'], 'similarity': r['similarity']} for r in rows]}")

    relevant_results = [r for r in rows if r['similarity'] is not None and r['similarity'] < 1.4]
    logger.info(f"Relevant results count: {len(relevant_results)}")

    if request.mode == "simple":
        if not relevant_results:
            logger.info("No results met similarity threshold")
            return [{
                "title": "No learnings found",
                "details": ["Try logging some learnings to see results here."],
                "code_snippet": ""
            }]

        formatted_results = []
        for r in relevant_results:
            result = {
                "title": r['description'],
                "details": [],
                "code_snippet": r['code_snippet']
            }
            if r['function_name']:
                result["details"].append(f" Function: {r['function_name']}")
            if r['library_name']:
                result["details"].append(f"Library: {r['library_name']}")
            result["details"].append(f"Match: {max(0, min(100, (1 - r['similarity']/2) * 100)):.0f}%")
            formatted_results.append(result)

        logger.info("=== RAG QUERY END (SIMPLE MODE) ===")
        return formatted_results

    # Powered mode
    logger.info("Processing powered mode...")
    conversation_context = "\n".join([
        f"{'User' if msg.is_user else 'Assistant'}: {msg.content}"
        for msg in request.conversation_history
    ]) or "No prior conversation available."

    learnings_context = (
        "Relevant code learnings that might help answer the question:\n" +
        "\n\n".join([
            f"Snippet {i+1}:\nDescription: {r['description']}\nCode:\n```\n{r['code_snippet']}\n```"
            for i, r in enumerate(relevant_results)
        ])
        if relevant_results else
        "No closely matching code examples found in your learnings."
    )


    if not relevant_results and not request.conversation_history:
        logger.info(f"User {current_user_id} submitted query with no learnings and no conversation. Proceeding with general LLM response.")

    #FINAL PROMPT FOR THE LLM
    logger.info("About to call LLM...")
    try:
        final_prompt = f"""You are a coding assistant focused on helping users understand and work with their code. You have access to their previous conversations and some of their code learnings.

        Previous conversation:
        {conversation_context}

        {learnings_context}

        Current question: {request.query}

        Instructions:
        1. Answer the question directly and concisely.
        2. When referencing code learnings, focus on the specific part of the code that is relevant to the question. WRAP ANY CODE BLOCKS IN ``` AND ANY IN-LINE CODE WITH `
        3. If none of the code learnings are relevant to the question, don't mention them at all.
        4. If the question is a follow-up, maintain context from the previous conversation.
        5. If you reference a code learning, explain why it's relevant to the question, using specific details from the code snippet when useful. Wrap any code used in response in ``` to make them more readable.
        6. When referencing a learning, use the full code block using the format above. When referencing a specific part of the code, you 
        7. Stay focused on programming-related topics.
        8. If no code learnings are available, provide a helpful answer based on your general knowledge.

        Answer:"""

        response = await call_gpt4_llm(final_prompt)
        logger.info("LLM call successful")
        print(response)
        logger.info("=== RAG QUERY END (POWERED MODE) ===")
        return {"response": response}
    except Exception as e:
        logger.error("LLM call failed:")
        logger.error(f"Error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to generate a response.")

#open AIs async client for API calls
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

#client for the openAI API
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#embeds the text into a vector (used when creating a new learning)
async def embed(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
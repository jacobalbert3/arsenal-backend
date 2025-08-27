# app/services/llm.py

import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#used in rag query to generate a response


#temperature = how creative the model is
#max_tokens = max number of tokens the model can return
async def call_gpt4_llm(prompt: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error from OpenAI: {e}")
        raise
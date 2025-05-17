# app/services/llm.py

import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

#openai.api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
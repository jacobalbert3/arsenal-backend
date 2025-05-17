# app/services/embedder.py
from sentence_transformers import SentenceTransformer

# Load once at startup
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed(text: str) -> list[float]:
    # Directly encode the text without instruction
    return model.encode(text).tolist()


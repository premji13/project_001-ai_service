"""Chatbot configuration for Groq, Pinecone, and LangChain."""
from os import getenv

# Groq configuration
GROQ_API_KEY = getenv("GROQ_API_KEY")
# GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MODEL = "openai/gpt-oss-120b"

# Pinecone configuration
PINECONE_API_KEY = getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_INDEX_NAME = getenv("PINECONE_INDEX_NAME", "chatbot-docs")

# LangChain configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# File upload constraints
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx'}

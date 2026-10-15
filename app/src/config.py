"""All settings come from environment variables so the same image runs in dev, qa and prod."""
import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "azure")          # azure | ollama
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")   # empty in cloud -> managed identity
CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT", "gpt-4.1-mini")
EMBED_DEPLOYMENT = os.getenv("EMBED_DEPLOYMENT", "text-embedding-3-small")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_CHAT = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1")
OLLAMA_EMBED = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

VECTOR_STORE = os.getenv("VECTOR_STORE", "chroma")      # chroma (local) | azure_search (cloud)
CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma")
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "fai-docs")

LANGFUSE_ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
ENV_NAME = os.getenv("APP_ENV", "local")

MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.3"))

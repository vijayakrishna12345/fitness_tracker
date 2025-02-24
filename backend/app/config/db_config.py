from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class QdrantSettings(BaseSettings):
    url: str = os.getenv("QDRANT_URL", "")
    api_key: str = os.getenv("QDRANT_API_KEY", "")
    collection_name: str = os.getenv("QDRANT_COLLECTION", "fitness_recommendations")
    vector_size: int = 1536  # OpenAI embedding size

    class Config:
        env_prefix = "QDRANT_"

class Neo4jSettings(BaseSettings):
    uri: str = os.getenv("NEO4J_URI", "")
    username: str = os.getenv("NEO4J_USERNAME", "")
    password: str = os.getenv("NEO4J_PASSWORD", "")
    database: str = os.getenv("NEO4J_DATABASE", "fitness")

    class Config:
        env_prefix = "NEO4J_"

class OpenAISettings(BaseSettings):
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-ada-002"
    )
    max_tokens: int = 8192
    batch_size: int = 100

    class Config:
        env_prefix = "OPENAI_"

# Initialize settings
qdrant_settings = QdrantSettings()
neo4j_settings = Neo4jSettings()
openai_settings = OpenAISettings()

# Validate required settings
if not all([qdrant_settings.url, qdrant_settings.api_key]):
    raise ValueError("Missing Qdrant configuration")

if not all([neo4j_settings.uri, neo4j_settings.username, neo4j_settings.password]):
    raise ValueError("Missing Neo4j configuration")

if not openai_settings.api_key:
    raise ValueError("Missing OpenAI API key")
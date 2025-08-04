# This is the complete and correct code for config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Pydantic will automatically read the variables from your .env file.
    # The values here are the defaults if a variable is NOT in your .env file.

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str

    # LlamaParse
    LLAMA_CLOUD_API_KEY: str

    # Google (Optional)
    GOOGLE_API_KEY: str | None = None

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_MULTIMODAL_MODEL: str = "llava"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        # Tell Pydantic to look for a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# This creates the settings object that your app uses.
# It will be correctly populated from your .env file now.
settings = Settings()
# This is the complete and correct code for config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- Required settings that MUST be in the .env file ---
    # Pydantic will raise an error on startup if these are not found.
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    LLAMA_CLOUD_API_KEY: str
    GOOGLE_API_KEY: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # --- Optional settings with sensible defaults ---
    # These will be used if they are not found in the .env file.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_MULTIMODAL_MODEL: str = "llava"

    class Config:
        # Tell Pydantic to look for a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# This creates the settings object that your app uses.
# It will be correctly populated from your .env file now.
settings = Settings()

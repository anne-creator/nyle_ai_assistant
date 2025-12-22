from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: Literal["local", "dev", "production"] = "local"
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # API Base URLs
    dev_api_base_url: str = "https://api0.dev.nyle.ai/math/v1"
    prod_api_base_url: str = "https://api.nyle.ai/math/v1"
    
    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_project: str = "nyle-chatbot"
    langchain_api_key: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def get_api_base_url(self) -> str:
        """Get base URL based on environment. Local and prod use prod URL."""
        if self.environment == "dev":
            return self.dev_api_base_url
        return self.prod_api_base_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    env = os.getenv("ENVIRONMENT", "local")
    env_file = f".env.{env}"
    settings = Settings(_env_file=env_file)
    
    # Set LangSmith environment variables for tracing
    # LangChain/LangGraph reads these from os.environ
    if settings.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_TRACING"] = "true"  # Also set the new variable name
    
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGSMITH_API_KEY"] = settings.langchain_api_key  # Also set the new variable name
    
    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGSMITH_PROJECT"] = settings.langchain_project  # Also set the new variable name
    
    return settings


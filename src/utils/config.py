"""
Configuration management using Pydantic settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # NVIDIA NIM Configuration
    nim_api_key: str = ""  # Will be validated by clients
    nim_inference_url: str = "https://integrate.api.nvidia.com/v1"
    nim_model: str = "llama-3.1-nemotron-nano-8b-instruct"
    nim_embedding_model: str = "nvidia/nv-embedqa-e5-v5"

    # Vector Database
    chroma_persist_dir: str = "./data/chroma"
    collection_name: str = "documents"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Agent Configuration
    max_iterations: int = 10
    temperature: float = 0.7
    max_tokens: int = 2048

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_account_id: Optional[str] = None
    eks_cluster_name: str = "nim-rag-agent-cluster"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env variables
    )


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fallback settings for when .env doesn't exist (e.g., during testing)
    import warnings
    warnings.warn(f"Could not load settings from .env: {e}. Using defaults.")
    settings = Settings(_env_file=None)

"""
Configuration management for Azure AI Infrastructure Platform

This module handles all configuration loading from environment variables
and provides type-safe access to configuration values.
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application settings
    app_name: str = Field(default="Azure AI Infrastructure Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_environment: str = Field(default="dev", description="Environment (dev, staging, prod)")
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload in development")

    # Azure OpenAI settings
    azure_openai_endpoint: Optional[str] = Field(None, description="Azure OpenAI endpoint URL")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", description="Azure OpenAI API version")
    azure_openai_chat_deployment: str = Field(default="gpt-4", description="Chat deployment name")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-ada-002", description="Embedding deployment name")
    azure_openai_api_key: Optional[str] = Field(None, description="Azure OpenAI API key (managed from Key Vault)")
    azure_client_id: Optional[str] = Field(None, description="Azure client ID for managed identity")

    # Azure Cognitive Search settings
    azure_search_endpoint: Optional[str] = Field(None, description="Azure Cognitive Search endpoint URL")
    azure_search_index: str = Field(default="ai-knowledge-base", description="Search index name")
    azure_search_api_key: Optional[str] = Field(None, description="Azure Search API key (managed from Key Vault)")

    # Azure Storage settings
    azure_storage_account: Optional[str] = Field(None, description="Azure Storage account name")
    azure_storage_container: str = Field(default="documents", description="Storage container name")
    azure_storage_connection_string: Optional[str] = Field(None, description="Storage connection string (managed from Key Vault)")

    # Azure Key Vault settings
    azure_key_vault_name: Optional[str] = Field(None, description="Azure Key Vault name")
    azure_tenant_id: Optional[str] = Field(None, description="Azure tenant ID")

    # Azure Monitor settings
    azure_app_insights_name: Optional[str] = Field(None, description="Application Insights name")
    azure_app_insights_instrumentation_key: Optional[str] = Field(None, description="Application Insights instrumentation key")
    azure_app_insights_connection_string: Optional[str] = Field(None, description="Application Insights connection string")

    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Max requests per minute")
    rate_limit_burst: int = Field(default=10, description="Max burst requests")

    # Cost tracking settings
    cost_tracking_enabled: bool = Field(default=True, description="Enable cost tracking")
    gpt4_input_cost_per_1k: float = Field(default=0.03, description="GPT-4 input cost per 1K tokens")
    gpt4_output_cost_per_1k: float = Field(default=0.06, description="GPT-4 output cost per 1K tokens")
    embedding_cost_per_1k: float = Field(default=0.0001, description="Embedding cost per 1K tokens")

    # Chat settings
    chat_max_tokens_default: int = Field(default=1000, description="Default max tokens for chat")
    chat_temperature_default: float = Field(default=0.7, description="Default temperature for chat")
    chat_max_tokens_limit: int = Field(default=4096, description="Maximum allowed tokens")

    # RAG settings
    rag_top_k_default: int = Field(default=5, description="Default number of top results")
    rag_min_score_default: float = Field(default=0.5, description="Default minimum relevance score")
    rag_top_k_limit: int = Field(default=10, description="Maximum allowed top-k")

    # Monitoring settings
    monitoring_enabled: bool = Field(default=True, description="Enable monitoring")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    metrics_retention_hours: int = Field(default=24, description="Metrics retention period in hours")

    # Security settings
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_methods: List[str] = Field(default=["*"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")

    @validator('app_environment')
    def validate_environment(cls, v):
        """Validate environment value"""
        valid_environments = ['dev', 'staging', 'prod']
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level value"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @validator('port')
    def validate_port(cls, v):
        """Validate port number"""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator('chat_temperature_default')
    def validate_temperature(cls, v):
        """Validate temperature value"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment variables"""
    global settings
    settings = Settings()
    return settings
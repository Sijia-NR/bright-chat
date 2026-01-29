import os
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    # Application settings
    APP_NAME: str = "Bright-Chat API"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Server settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    SERVER_WORKERS: int = 1
    SERVER_KEEPALIVE: int = 30
    SERVER_TIMEOUT: int = 30

    # CORS settings
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]

    # Database settings
    DB_DRIVER: str = "mysql"
    DB_HOST: str = "47.116.218.206"
    DB_PORT: int = 13306
    DB_USERNAME: str = "root"
    DB_PASSWORD: str = "123456"
    DB_DATABASE: str = "bright_chat"
    DB_CHARSET: str = "utf8mb4"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DECODE_RESPONSES: bool = True

    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # IAS settings - MockServer for LLM service simulation
    IAS_BASE_URL: str = "http://localhost:18063"
    IAS_APP_KEY: str = "APP_KEY"
    IAS_TIMEOUT: int = 30
    IAS_MAX_RETRIES: int = 3
    IAS_STREAM_CHUNK_SIZE: int = 1024
    IAS_API_FORMAT: str = "default"  # API format: default, openai, etc.

    # ChromaDB settings
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8002

    # RAG settings
    RAG_USE_CHROMADB_EMBEDDING: bool = False
    BGE_MODEL_PATH: str = "/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_FILE_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: int = 5

    # Monitoring settings
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PATH: str = "/metrics"

    # OpenAPI settings
    OPENAPI_TITLE: str = "Bright-Chat API"
    OPENAPI_DESCRIPTION: str = "Bright-Chat Backend API Documentation"
    OPENAPI_VERSION: str = "1.0.0"
    OPENAPI_CONTACT_NAME: str = "Bright-Chat Team"
    OPENAPI_CONTACT_EMAIL: str = "api@bright-chat.com"
    OPENAPI_LICENSE_NAME: str = "MIT"
    OPENAPI_LICENSE_URL: str = "https://opensource.org/licenses/MIT"

    # Feature settings
    ENABLE_MOCK_DATA: bool = False
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_DRIVER == "mysql":
            return f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}?charset={self.DB_CHARSET}"
        elif self.DB_DRIVER == "postgresql":
            return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        else:
            raise ValueError(f"Unsupported database driver: {self.DB_DRIVER}")

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"


settings = Settings()
"""
FastAPI Backend Configuration
Manage environment variables and application settings
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # ============================================================
    # Server Configuration
    # ============================================================
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")
    workers: int = Field(default=1, description="Number of worker processes")

    # ============================================================
    # CORS Configuration
    # ============================================================
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials")
    cors_methods: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    cors_headers: list[str] = Field(default=["*"], description="Allowed headers")

    # ============================================================
    # Storage Configuration
    # ============================================================
    data_dir: str = Field(default="./data", description="Data directory path")
    store_file: str = Field(default="store.json", description="Store file name")

    # ============================================================
    # Application Settings
    # ============================================================
    app_name: str = Field(default="Revision Backend", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=True, description="Debug mode")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment type",
    )

    class Config:
        """Pydantic settings configuration"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def store_path(self) -> str:
        """Get full path to store file"""
        return os.path.join(self.data_dir, self.store_file)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()

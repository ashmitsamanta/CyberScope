import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "CYBERSCOPE"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database: SQLite default for friction-free local execution; supports PostgreSQL
    DATABASE_URL: str = "sqlite:///./cyberscope.db"

    # Graph layer: networkx (in-memory synchronized with relational store) or neo4j
    GRAPH_BACKEND: str = "networkx"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "cyberscope_neo4j"

    # AI Provider: fallback (deterministic explainable expert engine) or openai
    AI_PROVIDER: str = "fallback"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Detection & Analysis Thresholds
    BURST_WINDOW_MINUTES: int = 15
    BURST_TRANSACTION_COUNT: int = 4
    FAN_OUT_THRESHOLD: int = 3
    FAN_IN_THRESHOLD: int = 3
    CIRCULAR_FLOW_MAX_HOPS: int = 5
    DORMANCY_DAYS_THRESHOLD: int = 30
    UNUSUAL_AMOUNT_RATIO: float = 3.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()

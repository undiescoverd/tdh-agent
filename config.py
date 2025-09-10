from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    google_api_key: str
    debug_mode: bool = False
    max_retries: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()
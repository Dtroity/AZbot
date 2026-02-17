import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str
    admins: list[int] = []
    
    # Database
    postgres_db: str = "supply"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        # Parse admins from comma-separated string
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "admins":
                return [int(x.strip()) for x in raw_val.split(",")]
            return None


settings = Settings()

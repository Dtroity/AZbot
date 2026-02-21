from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (в Docker: POSTGRES_* из docker-compose; pydantic-settings ищет POSTGRES_DB, POSTGRES_HOST и т.д.)
    postgres_db: str = "supply"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    @property
    def database_url(self) -> str:
        pwd = (self.postgres_password or "").strip() or "postgres"
        return f"postgresql+asyncpg://{self.postgres_user}:{pwd}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

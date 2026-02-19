from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str
    admins: list[int] = []

    @field_validator("admins", mode="before")
    @classmethod
    def parse_admins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return []

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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()

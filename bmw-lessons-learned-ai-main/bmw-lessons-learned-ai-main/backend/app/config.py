from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./lessons_learned.db"

    # OpenAI
    openai_api_key: str

    # File Upload
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: str = "image/jpeg,image/png,application/pdf"

    # App Settings
    app_name: str = "Lessons Learned API"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

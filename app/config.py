from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_type: str
    database_username: str
    database_password: str
    database_host: str
    database_port: int
    database_name: str

    #Redis
    redis_host: str
    redis_port: int
    redis_db: int

    #OpenAI
    openai_api_key: str
    embedding_model: str
    
    # Other settings
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
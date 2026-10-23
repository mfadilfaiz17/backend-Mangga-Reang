from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "API Juragan Mangga Reang"
    VERSION: str = "1.0.0"
    
    # URL Database (Ganti username & password sesuai Postgres kamu)
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/mangga_db"
    
    # Secret Key untuk JWT Token
    SECRET_KEY: str = "super_secret_key_jangan_dibocorkan_ke_github"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
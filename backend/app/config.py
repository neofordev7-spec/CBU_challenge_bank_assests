from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Bank Asset Management"
    DATABASE_URL: str = "sqlite:///./bank_assets.db"
    SECRET_KEY: str = "hackathon-secret-key-2026-bank-assets"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    UPLOAD_DIR: str = "uploads"
    QRCODE_DIR: str = "qrcodes"
    BASE_URL: str = "http://localhost:8000"
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()

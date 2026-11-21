from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"
    FIREBASE_PROJECT_ID: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# What this does?
# Added FIREBASE_PROJECT_ID: str.
# Python will now load the project ID from your MCP .env.
# The existing backend URL configuration remains unchanged.
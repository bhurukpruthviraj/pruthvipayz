from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    razorpay_key_id: str
    razorpay_key_secret: str
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
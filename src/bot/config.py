from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(min_length=1)
    webhook_url: str = Field(min_length=1)
    # Telegram secret_token: 1-256 chars; require enough entropy to be meaningful
    webhook_secret: str = Field(min_length=16)
    webhook_path: str = "/webhook"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    webhook_url: str
    webhook_secret: str
    webhook_path: str = "/webhook"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

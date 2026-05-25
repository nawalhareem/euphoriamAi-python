from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_model_mini: str = "gpt-4o-mini"
    ai_internal_key: str = ""
    port: int = 8000


settings = Settings()

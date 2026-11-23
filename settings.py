from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

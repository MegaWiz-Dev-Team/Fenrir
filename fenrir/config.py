"""Configuration — loads settings from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Fenrir application settings."""

    # Server
    fenrir_host: str = "127.0.0.1"
    fenrir_port: int = 8200
    log_level: str = "info"

    # OpenEMR / Eir
    openemr_url: str = "http://localhost:80"
    openemr_fhir_url: str = "http://localhost:80/apis/default/fhir"
    openemr_auth_token: str = ""

    # Heimdall LLM Gateway
    heimdall_url: str = "http://localhost:8080"

    # Browser Use
    browser_headless: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

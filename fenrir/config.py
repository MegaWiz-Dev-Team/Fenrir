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

    # Browser / Ratatoskr
    browser_headless: bool = True
    ratatoskr_url: str = "http://localhost:9200"

    # OpenEMR Messaging (Message Center integration)
    openemr_api_url: str = "http://localhost:80/apis/default/api"
    openemr_client_id: str = ""
    openemr_client_secret: str = ""
    message_poll_interval: int = 15  # seconds
    fenrir_username: str = "fenrir-ai"
    message_enabled: bool = False  # Feature flag

    # Mimir Knowledge Base
    mimir_url: str = "http://localhost:4200"

    # Forseti E2E Dashboard
    forseti_url: str = "http://forseti:5555"

    # Authentication (Yggdrasil)
    auth_enabled: bool = True
    yggdrasil_issuer: str = "http://localhost:8085"
    jwt_audience: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

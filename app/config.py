from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env only when present. CI and GitHub Codespaces inject NEO4J_* via the environment.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j — matches GitHub Actions / Codespaces secret names (injected as env, no runtime GitHub API).
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        validation_alias="NEO4J_URI",
    )
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_USERNAME", "NEO4J_USER"),
    )
    neo4j_password: str = Field(
        default="",
        validation_alias="NEO4J_PASSWORD",
    )
    neo4j_database: str = Field(
        default="neo4j",
        validation_alias="NEO4J_DATABASE",
    )

    # Neo4j Aura metadata (optional; not used by the driver)
    aura_instance_id: str = Field(default="", validation_alias="AURA_INSTANCEID")
    aura_instance_name: str = Field(default="", validation_alias="AURA_INSTANCENAME")

    # RocketRide AI
    rocketride_uri: str = "http://localhost:5565"
    rocketride_apikey: str = ""

    # Bland AI Voice Agent
    bland_api_key: str = ""

    # GMI Cloud Inference
    gmi_base_url: str = "https://api.gmi-serving.com/v1"
    gmi_api_key: str = ""
    gmi_model: str = "deepseek-ai/DeepSeek-R1"

    # App
    base_url: str = "http://localhost:8000"
    skip_auth: bool = True


settings = Settings()

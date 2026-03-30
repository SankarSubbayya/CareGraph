from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j — env: NEO4J_URI, NEO4J_USERNAME (or NEO4J_USER), NEO4J_PASSWORD, NEO4J_DATABASE
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_USERNAME", "NEO4J_USER"),
    )
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

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

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", validation_alias=AliasChoices("NEO4J_URI"))
    neo4j_user: str = Field(default="neo4j", validation_alias=AliasChoices("NEO4J_USER", "NEO4J_USERNAME"))
    neo4j_password: str = Field(default="", validation_alias=AliasChoices("NEO4J_PASSWORD"))
    neo4j_database: str | None = Field(default=None, validation_alias=AliasChoices("NEO4J_DATABASE"))

    # RocketRide AI
    rocketride_uri: str = "http://localhost:5565"
    rocketride_apikey: str = ""

    # Bland AI Voice Agent
    bland_api_key: str = ""

    # GMI Cloud Inference
    gmi_base_url: str = "https://api.gmi-serving.com/v1"
    gmi_api_key: str = ""
    gmi_model: str = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"

    # App
    base_url: str = "http://localhost:8000"
    skip_auth: bool = True
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    environment: str = "development"

    # Optional demo protection
    demo_username: str = ""
    demo_password: str = ""

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def demo_auth_enabled(self) -> bool:
        return bool(self.demo_username and self.demo_password)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


settings = Settings()

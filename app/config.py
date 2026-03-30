from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "careGraph2026"

    # RocketRide AI
    rocketride_uri: str = "http://localhost:5565"
    rocketride_apikey: str = ""

    # GMI Cloud Inference
    gmi_base_url: str = "https://api.gmi-serving.com/v1"
    gmi_api_key: str = ""
    gmi_model: str = "deepseek-ai/DeepSeek-R1"

    # App
    base_url: str = "http://localhost:8000"
    skip_auth: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

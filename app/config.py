from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

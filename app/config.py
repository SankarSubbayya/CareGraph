from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # RocketRide — one webhook URL per pipeline (empty = use rocketride_uri + /webhook)
    rocketride_uri: str = "http://localhost:5565"
    rocketride_apikey: str = ""
    rocketride_checkin_webhook_url: str = ""
    rocketride_drug_interaction_webhook_url: str = ""
    rocketride_care_recommendation_webhook_url: str = ""
    rocketride_condition_suggestion_webhook_url: str = ""

    # Bland AI Voice Agent
    bland_api_key: str = ""

    # GMI Cloud Inference (fallback when RocketRide fails)
    gmi_base_url: str = "https://api.gmi-serving.com/v1"
    gmi_api_key: str = ""
    gmi_model: str = "deepseek-ai/DeepSeek-R1"

    # App
    base_url: str = "http://localhost:8000"
    skip_auth: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

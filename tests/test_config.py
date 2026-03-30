"""Unit tests for configuration."""

from app.config import Settings


def test_default_settings(monkeypatch):
    """Test that defaults work when no .env is loaded."""
    # Clear env vars that .env would set
    for key in ("NEO4J_URI", "NEO4J_PASSWORD", "GMI_API_KEY", "BLAND_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    s = Settings(neo4j_password="test", _env_file=None)
    assert s.neo4j_user == "neo4j"
    assert s.rocketride_uri == "http://localhost:5565"
    assert s.rocketride_apikey == ""
    assert s.rocketride_checkin_webhook_url == ""
    assert s.rocketride_drug_interaction_webhook_url == ""
    assert s.gmi_base_url == "https://api.gmi-serving.com/v1"
    assert s.gmi_model == "deepseek-ai/DeepSeek-R1"
    assert s.skip_auth is True


def test_settings_override():
    s = Settings(
        neo4j_uri="neo4j+s://test.databases.neo4j.io",
        neo4j_password="secret",
        gmi_api_key="test-key",
        bland_api_key="org_test",
        _env_file=None,
    )
    assert s.neo4j_uri == "neo4j+s://test.databases.neo4j.io"
    assert s.gmi_api_key == "test-key"
    assert s.bland_api_key == "org_test"

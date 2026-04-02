"""Unit tests for configuration."""

from app.config import Settings

# Env vars that .env sets and that would override test values
_ENV_KEYS = (
    "NEO4J_URI", "NEO4J_USER", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE",
    "GMI_API_KEY", "GMI_BASE_URL", "GMI_MODEL",
    "BLAND_API_KEY", "ROCKETRIDE_URI", "ROCKETRIDE_APIKEY",
    "BASE_URL", "ENVIRONMENT", "CORS_ORIGINS",
    "DEMO_USERNAME", "DEMO_PASSWORD", "ADMIN_API_TOKEN",
)


def _clear_env(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_default_settings(monkeypatch):
    """Test that defaults work when no .env is loaded."""
    _clear_env(monkeypatch)

    s = Settings(neo4j_password="test", _env_file=None)
    assert s.neo4j_user == "neo4j"
    assert s.rocketride_uri == "http://localhost:5565"
    assert s.gmi_base_url == "https://api.gmi-serving.com/v1"
    assert s.gmi_model == "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
    assert s.skip_auth is True


def test_settings_override(monkeypatch):
    _clear_env(monkeypatch)

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


def test_aura_env_names_are_normalized(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://62ec3403.databases.neo4j.io")
    monkeypatch.setenv("NEO4J_USERNAME", "62ec3403")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    monkeypatch.setenv("NEO4J_DATABASE", "62ec3403")

    s = Settings(_env_file=None)
    assert s.neo4j_uri == "neo4j+s://62ec3403.databases.neo4j.io"
    assert s.neo4j_user == "62ec3403"
    assert s.neo4j_database == "62ec3403"

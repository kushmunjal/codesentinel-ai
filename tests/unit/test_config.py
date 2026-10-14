import pytest
from pydantic import ValidationError

from codesentinel.config import CheckSettings, CodeSentinelConfig, load_config


def test_default_config():
    config = CodeSentinelConfig()
    assert config.provider == "groq"
    assert config.model == "qwen/qwen3.8-27b"
    assert config.fallback_model == "openai/gpt-oss-120b"
    assert config.base_url == "https://api.groq.com/openai/v1"
    assert config.severity_threshold == "high"
    assert config.verbosity == "detailed"
    assert config.max_files == 50
    assert config.token_budget == 100000
    assert config.cost_budget_usd == 1.00
    assert "package-lock.json" in config.ignore_paths
    assert config.enabled_checks.secrets is True

def test_load_config_from_custom_yaml(tmp_path):
    yaml_file = tmp_path / "custom.yml"
    yaml_file.write_text("""
provider: "openai"
model: "gpt-4o"
fallback_model: "gpt-4o-mini"
base_url: "https://api.openai.com/v1"
severity_threshold: "medium"
verbosity: "compact"
max_files: 30
guidelines:
  - "Always add type hints"
  - "Write unit tests for new helpers"
""")
    config = load_config(str(yaml_file))
    assert config.provider == "openai"
    assert config.model == "gpt-4o"
    assert config.fallback_model == "gpt-4o-mini"
    assert config.severity_threshold == "medium"
    assert config.verbosity == "compact"
    assert config.max_files == 30
    assert len(config.guidelines) == 2
    assert "Always add type hints" in config.guidelines

def test_load_config_environment_variable_overrides(tmp_path, monkeypatch):
    yaml_file = tmp_path / "settings.yml"
    yaml_file.write_text("provider: groq\nmodel: llama3\n")
    
    monkeypatch.setenv("PROVIDER", "anthropic")
    monkeypatch.setenv("MODEL", "claude-3-7-sonnet")
    monkeypatch.setenv("FALLBACK_MODEL", "claude-3-5-haiku")
    monkeypatch.setenv("BASE_URL", "https://api.anthropic.com/v1")
    monkeypatch.setenv("API_KEY", "secret-test-key")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_123456789")
    monkeypatch.setenv("SEVERITY_THRESHOLD", "LOW")
    monkeypatch.setenv("VERBOSITY", "COMPACT")
    
    config = load_config(str(yaml_file))
    assert config.provider == "anthropic"
    assert config.model == "claude-3-7-sonnet"
    assert config.fallback_model == "claude-3-5-haiku"
    assert config.base_url == "https://api.anthropic.com/v1"
    assert config.api_key == "secret-test-key"
    assert config.github_token == "ghp_123456789"
    assert config.severity_threshold == "low"
    assert config.verbosity == "compact"

def test_load_config_invalid_yaml_syntax_falls_back(tmp_path, capsys):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("provider: [unclosed")
    
    config = load_config(str(bad_yaml))
    captured = capsys.readouterr()
    assert "Warning: Failed to parse config file" in captured.out
    assert config.provider == "groq"

def test_load_config_validation_error(monkeypatch):
    monkeypatch.setenv("SEVERITY_THRESHOLD", "unsupported_level")
    with pytest.raises(ValidationError):
        load_config("nonexistent.yml")

def test_check_settings_custom():
    settings = CheckSettings(secrets=True, heuristics=False, bugs=True, performance=False)
    assert settings.secrets is True
    assert settings.heuristics is False
    assert settings.performance is False

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
import os
import yaml

class CheckSettings(BaseModel):
    secrets: bool = True
    heuristics: bool = True
    bugs: bool = True
    performance: bool = True
    style: bool = True
    tests: bool = True

class CodeSentinelConfig(BaseModel):
    provider: str = Field(default="groq", description="LLM provider: groq, openai, etc.")
    model: str = Field(default="qwen/qwen3.8-27b", description="Primary LLM model ID")
    fallback_model: Optional[str] = Field(default="openai/gpt-oss-120b", description="Fallback LLM model ID")
    base_url: str = Field(default="https://api.groq.com/openai/v1", description="OpenAI-compatible Base URL")
    api_key: Optional[str] = Field(default=None, description="API Key for LLM provider")
    github_token: Optional[str] = Field(default=None, description="GitHub Token")
    
    ignore_paths: List[str] = Field(
        default_factory=lambda: [
            "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "Cargo.lock",
            "dist/*", "build/*", ".next/*", "*.min.js", "*.min.css", "*.map", "*.svg", "*.png", "*.jpg"
        ]
    )
    severity_threshold: Literal["low", "medium", "high", "critical"] = Field(
        default="high", description="Minimum severity to mark PR as Needs Attention"
    )
    enabled_checks: CheckSettings = Field(default_factory=CheckSettings)
    custom_labels: Dict[str, str] = Field(
        default_factory=lambda: {
            "bug": "bug",
            "enhancement": "enhancement",
            "question": "question",
            "duplicate": "duplicate"
        }
    )
    review_language: str = Field(default="en")
    max_files: int = Field(default=50, description="Max files to review in single PR")
    max_tokens_per_chunk: int = Field(default=2000)
    token_budget: int = Field(default=100000, description="Max tokens per review run")
    cost_budget_usd: float = Field(default=1.00, description="Max dollar budget per review run")
    secret_allowlist: List[str] = Field(default_factory=list, description="Regex or string patterns to ignore in secret scanning")
    guidelines: List[str] = Field(default_factory=list, description="Repository-specific rules")
    verbosity: Literal["compact", "detailed"] = Field(default="detailed")

def load_config(config_path: Optional[str] = None) -> CodeSentinelConfig:
    """Loads config from YAML file, overrides with environment variables, falls back to defaults."""
    data = {}
    
    # 1. Load from file if specified or found
    path = config_path or os.environ.get("CONFIG_PATH", ".codesentinel.yml")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception as e:
            print(f"Warning: Failed to parse config file at {path}: {e}")

    # 2. Environment variable overrides (higher precedence)
    if os.environ.get("PROVIDER"):
        data["provider"] = os.environ["PROVIDER"]
    if os.environ.get("MODEL"):
        data["model"] = os.environ["MODEL"]
    if os.environ.get("FALLBACK_MODEL"):
        data["fallback_model"] = os.environ["FALLBACK_MODEL"]
    if os.environ.get("BASE_URL"):
        data["base_url"] = os.environ["BASE_URL"]
    if os.environ.get("API_KEY"):
        data["api_key"] = os.environ["API_KEY"]
    if os.environ.get("GITHUB_TOKEN"):
        data["github_token"] = os.environ["GITHUB_TOKEN"]
    if os.environ.get("SEVERITY_THRESHOLD"):
        data["severity_threshold"] = os.environ["SEVERITY_THRESHOLD"].lower()
    if os.environ.get("VERBOSITY"):
        data["verbosity"] = os.environ["VERBOSITY"].lower()

    try:
        return CodeSentinelConfig(**data)
    except ValidationError as err:
        print(f"Configuration error: {err}")
        raise

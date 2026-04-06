"""Data models for Claude model configurations."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for a single model set."""

    name: str = ""
    base_url: str = ""
    api_key: str = ""
    auth_token: str = ""
    opus_model: str = ""
    sonnet_model: str = ""
    haiku_model: str = ""

    def to_env_vars(self) -> dict[str, str]:
        """Convert to environment variable dict (only non-empty values)."""
        env = {
            "ANTHROPIC_BASE_URL": self.base_url,
            "ANTHROPIC_API_KEY": self.api_key,
            "ANTHROPIC_AUTH_TOKEN": self.auth_token,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": self.opus_model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": self.sonnet_model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": self.haiku_model,
        }
        return {k: v for k, v in env.items() if v}

    def to_yaml_dict(self) -> dict:
        """Convert to YAML-serializable dict (only non-empty values)."""
        non_empty = {
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "auth_token": self.auth_token,
            "opus_model": self.opus_model,
            "sonnet_model": self.sonnet_model,
            "haiku_model": self.haiku_model,
        }
        return {k: v for k, v in non_empty.items() if v}


@dataclass
class ConfigFile:
    """Complete configuration file with all models."""

    active: Optional[str] = None
    models: dict[str, ModelConfig] = field(default_factory=dict)

    def get_active(self) -> Optional[ModelConfig]:
        """Get the currently active model config."""
        if self.active and self.active in self.models:
            return self.models[self.active]
        return None

    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a specific model config by name."""
        return self.models.get(name)

    def set_active(self, name: str) -> bool:
        """Set the active model. Returns True if successful."""
        if name in self.models:
            self.active = name
            return True
        return False

    def to_yaml_dict(self) -> dict:
        """Convert to YAML-serializable dict."""
        data = {}
        if self.active:
            data["active"] = self.active
        if self.models:
            data["models"] = {name: config.to_yaml_dict() for name, config in self.models.items()}
        return data

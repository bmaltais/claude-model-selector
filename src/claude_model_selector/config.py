"""Configuration file management."""

import os
from pathlib import Path
from typing import Optional

import yaml

from .models import ConfigFile, ModelConfig

DEFAULT_CONFIG_DIR = Path.home() / ".claude" / "model-config"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "models.yaml"


def get_config_path() -> Path:
    """Get the configuration file path, respecting env override."""
    env_path = os.environ.get("CLAUDE_MODEL_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_CONFIG_FILE


def ensure_config_dir() -> Path:
    """Ensure the config directory exists."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    return config_path.parent


def load_config() -> ConfigFile:
    """Load the configuration file."""
    config_path = get_config_path()
    default = ConfigFile()

    if not config_path.exists():
        return default

    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}

    config = ConfigFile()
    config.active = data.get("active")

    models_data = data.get("models", {})
    for name, model_data in models_data.items():
        config.models[name] = ModelConfig(
            name=model_data.get("name", ""),
            base_url=model_data.get("base_url", ""),
            api_key=model_data.get("api_key", ""),
            auth_token=model_data.get("auth_token", ""),
            opus_model=model_data.get("opus_model", ""),
            sonnet_model=model_data.get("sonnet_model", ""),
            haiku_model=model_data.get("haiku_model", ""),
        )

    return config


def save_config(config: ConfigFile) -> None:
    """Save the configuration file."""
    ensure_config_dir()
    config_path = get_config_path()

    with open(config_path, "w") as f:
        yaml.dump(config.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)


def add_model(name: str, model: ModelConfig) -> None:
    """Add or update a model configuration."""
    config = load_config()
    # Use the key name if no description was set, otherwise keep the description
    if not model.name or model.name == name:
        model.name = name
    config.models[name] = model
    save_config(config)


def remove_model(name: str) -> bool:
    """Remove a model configuration. Returns True if removed."""
    config = load_config()
    if name in config.models:
        del config.models[name]
        if config.active == name:
            config.active = None
        save_config(config)
        return True
    return False


def get_model(name: str) -> Optional[ModelConfig]:
    """Get a model configuration by name."""
    config = load_config()
    return config.get_model(name)


def list_models() -> dict[str, ModelConfig]:
    """List all configured models."""
    config = load_config()
    return config.models


def get_active_model() -> Optional[ModelConfig]:
    """Get the currently active model."""
    config = load_config()
    return config.get_active()


def set_active(name: str) -> bool:
    """Set the active model. Returns True if successful."""
    config = load_config()
    if config.set_active(name):
        save_config(config)
        return True
    return False

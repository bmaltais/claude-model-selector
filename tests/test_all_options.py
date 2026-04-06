"""Comprehensive tests for all model configuration options."""

import os
from pathlib import Path

import pytest

from claude_model_selector.models import ConfigFile, ModelConfig
from claude_model_selector.config import (
    load_config,
    save_config,
    add_model,
    get_model,
    set_active,
    get_config_path,
    DEFAULT_CONFIG_FILE,
)
from claude_model_selector.cli import main
from click.testing import CliRunner


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory and set the environment variable."""
    original_env = os.environ.get("CLAUDE_MODEL_CONFIG_PATH")
    config_dir = tmp_path / "model-config"
    config_dir.mkdir()
    config_path = config_dir / "models.yaml"
    os.environ["CLAUDE_MODEL_CONFIG_PATH"] = str(config_path)
    yield config_path
    if original_env:
        os.environ["CLAUDE_MODEL_CONFIG_PATH"] = original_env
    elif "CLAUDE_MODEL_CONFIG_PATH" in os.environ:
        del os.environ["CLAUDE_MODEL_CONFIG_PATH"]


class TestModelConfigToEnvVars:
    """Test the to_env_vars() method for all configuration options."""

    def test_all_options(self):
        """Test that all options are converted to environment variables."""
        model = ModelConfig(
            name="test-model",
            base_url="https://custom.api.com",
            api_key="test-api-key-123",
            auth_token="test-auth-token-456",
            opus_model="claude-3-opus",
            sonnet_model="claude-3-sonnet",
            haiku_model="claude-3-haiku",
        )
        env = model.to_env_vars()

        assert env["ANTHROPIC_BASE_URL"] == "https://custom.api.com"
        assert env["ANTHROPIC_API_KEY"] == "test-api-key-123"
        assert env["ANTHROPIC_AUTH_TOKEN"] == "test-auth-token-456"
        assert env["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "claude-3-opus"
        assert env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "claude-3-sonnet"
        assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "claude-3-haiku"

    def test_empty_config(self):
        """Test that empty config produces no env vars."""
        model = ModelConfig()
        env = model.to_env_vars()
        assert env == {}

    def test_partial_config(self):
        """Test that only non-empty values are included."""
        model = ModelConfig(
            name="test",
            base_url="https://test.com",
            api_key="",
            auth_token="",
            opus_model="claude-3-opus",
            sonnet_model="",
            haiku_model="",
        )
        env = model.to_env_vars()

        assert "ANTHROPIC_BASE_URL" in env
        assert "ANTHROPIC_API_KEY" not in env
        assert "ANTHROPIC_AUTH_TOKEN" not in env
        assert "ANTHROPIC_DEFAULT_OPUS_MODEL" in env
        assert "ANTHROPIC_DEFAULT_SONNET_MODEL" not in env
        assert "ANTHROPIC_DEFAULT_HAIKU_MODEL" not in env


class TestModelConfigToYamlDict:
    """Test the to_yaml_dict() method for all configuration options."""

    def test_all_options(self):
        """Test YAML serialization of all options."""
        model = ModelConfig(
            name="test-model",
            base_url="https://custom.api.com",
            api_key="test-api-key",
            auth_token="test-auth-token",
            opus_model="claude-3-opus",
            sonnet_model="claude-3-sonnet",
            haiku_model="claude-3-haiku",
        )
        data = model.to_yaml_dict()

        assert data["name"] == "test-model"
        assert data["base_url"] == "https://custom.api.com"
        assert data["api_key"] == "test-api-key"
        assert data["auth_token"] == "test-auth-token"
        assert data["opus_model"] == "claude-3-opus"
        assert data["sonnet_model"] == "claude-3-sonnet"
        assert data["haiku_model"] == "claude-3-haiku"

    def test_empty_config(self):
        """Test that empty config produces minimal YAML."""
        model = ModelConfig(name="test")
        data = model.to_yaml_dict()
        assert data == {"name": "test"}


class TestConfigFileOperations:
    """Test configuration file save/load operations."""

    def test_save_and_load_full_config(self, temp_config_dir):
        """Test saving and loading a complete config."""
        config = ConfigFile(
            active="local",
            models={
                "local": ModelConfig(
                    name="Local LLM",
                    base_url="http://localhost:8080",
                    api_key="",
                    auth_token="my-token",
                    opus_model="Qwen/Qwen3.5-35B-A3B-FP8",
                    sonnet_model="local-model-sonnet",
                    haiku_model="local-model-haiku",
                ),
                "cloud": ModelConfig(
                    name="Anthropic Cloud",
                    base_url="https://api.anthropic.com",
                    api_key="sk-ant-123",
                    auth_token="",
                    opus_model="claude-3-opus",
                    sonnet_model="claude-3-sonnet",
                    haiku_model="claude-3-haiku",
                ),
            },
        )
        save_config(config)

        loaded = load_config()
        assert loaded.active == "local"
        assert "local" in loaded.models
        assert "cloud" in loaded.models
        assert loaded.models["local"].base_url == "http://localhost:8080"
        assert loaded.models["local"].auth_token == "my-token"
        assert loaded.models["local"].opus_model == "Qwen/Qwen3.5-35B-A3B-FP8"

    def test_save_load_yaml_format(self, temp_config_dir):
        """Verify YAML output format matches expectations."""
        model = ModelConfig(
            name="My Model",
            base_url="http://localhost:8000",
            api_key="key123",
            auth_token="token456",
            opus_model="opus-v1",
            sonnet_model="sonnet-v1",
            haiku_model="haiku-v1",
        )
        config = ConfigFile(active="test", models={"test": model})
        save_config(config)

        # Verify YAML file content
        content = temp_config_dir.read_text()
        assert "test:" in content
        assert "active: test" in content
        assert "name: My Model" in content
        assert "base_url: http://localhost:8000" in content
        assert "api_key: key123" in content
        assert "auth_token: token456" in content
        assert "opus_model: opus-v1" in content


class TestCLIAddCommand:
    """Test the CLI add command with all options."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_add_with_all_options(self, temp_config_dir, runner):
        """Test adding a model with all CLI options."""
        result = runner.invoke(
            main,
            [
                "add",
                "local-test",
                "--base-url",
                "http://localhost:8080",
                "--api-key",
                "my-api-key",
                "--auth-token",
                "my-auth-token",
                "--opus-model",
                "qwen-opus",
                "--sonnet-model",
                "qwen-sonnet",
                "--haiku-model",
                "qwen-haiku",
                "--description",
                "Local Qwen Model",
            ],
        )
        assert result.exit_code == 0
        assert "Added model configuration: local-test" in result.output

        model = get_model("local-test")
        assert model is not None
        # description becomes the display name stored in model.name
        assert model.name == "Local Qwen Model"
        assert model.base_url == "http://localhost:8080"
        assert model.api_key == "my-api-key"
        assert model.auth_token == "my-auth-token"
        assert model.opus_model == "qwen-opus"
        assert model.sonnet_model == "qwen-sonnet"
        assert model.haiku_model == "qwen-haiku"

    def test_add_minimal(self, temp_config_dir, runner):
        """Test adding a model with minimal options."""
        result = runner.invoke(
            main,
            ["add", "minimal", "--description", "Minimal Model"],
        )
        assert result.exit_code == 0
        model = get_model("minimal")
        assert model.name == "Minimal Model"
        assert model.base_url == ""
        assert model.api_key == ""
        assert model.auth_token == ""

    def test_add_with_base_url_only(self, temp_config_dir, runner):
        """Test adding a model with just base URL."""
        result = runner.invoke(
            main,
            ["add", "local", "--base-url", "http://localhost:3000", "--opus-model", "local-llm"],
        )
        assert result.exit_code == 0
        model = get_model("local")
        assert model.base_url == "http://localhost:3000"
        assert model.opus_model == "local-llm"


class TestCLIEditCommand:
    """Test the CLI edit command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_edit_single_field(self, temp_config_dir, runner):
        """Test editing a single field."""
        # First add a model
        runner.invoke(
            main,
            ["add", "test", "--description", "Test Model", "--opus-model", "opus-old"],
        )

        # Edit just the opus model
        result = runner.invoke(
            main,
            ["edit", "test", "--opus-model", "opus-new"],
        )
        assert result.exit_code == 0

        model = get_model("test")
        assert model.opus_model == "opus-new"
        assert model.name == "Test Model"

    def test_edit_multiple_fields(self, temp_config_dir, runner):
        """Test editing multiple fields at once."""
        runner.invoke(main, ["add", "test", "--description", "Test"])

        result = runner.invoke(
            main,
            [
                "edit",
                "test",
                "--base-url",
                "http://new.url.com",
                "--api-key",
                "new-key",
                "--sonnet-model",
                "new-sonnet",
            ],
        )
        assert result.exit_code == 0

        model = get_model("test")
        assert model.base_url == "http://new.url.com"
        assert model.api_key == "new-key"
        assert model.sonnet_model == "new-sonnet"

    def test_edit_nonexistent_model(self, temp_config_dir, runner):
        """Test editing a model that doesn't exist."""
        result = runner.invoke(main, ["edit", "nonexistent", "--base-url", "http://test.com"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestCLIShowCommand:
    """Test the CLI show command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_show_all_fields(self, temp_config_dir, runner):
        """Test show with all fields populated."""
        runner.invoke(
            main,
            [
                "add",
                "full",
                "--description",
                "Full Model",
                "--base-url",
                "http://localhost:8000",
                "--api-key",
                "secret123",
                "--auth-token",
                "token456",
                "--opus-model",
                "opus-model",
                "--sonnet-model",
                "sonnet-model",
                "--haiku-model",
                "haiku-model",
            ],
        )
        runner.invoke(main, ["select", "full"])

        result = runner.invoke(main, ["show"])
        assert result.exit_code == 0
        assert "Full Model" in result.output
        assert "http://localhost:8000" in result.output
        assert "*******" in result.output  # Masked key/token


class TestCLIExportCommand:
    """Test the CLI export command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_export_all_options(self, temp_config_dir, runner):
        """Test export with all options."""
        runner.invoke(
            main,
            [
                "add",
                "export-test",
                "--base-url",
                "http://localhost:9000",
                "--api-key",
                "api-key-123",
                "--auth-token",
                "auth-token-456",
                "--opus-model",
                "opus-test",
                "--sonnet-model",
                "sonnet-test",
                "--haiku-model",
                "haiku-test",
            ],
        )
        runner.invoke(main, ["select", "export-test"])

        result = runner.invoke(main, ["export"])
        assert result.exit_code == 0

        # Verify all exports
        lines = result.output.strip().split("\n")
        assert any("ANTHROPIC_BASE_URL='http://localhost:9000'" in line for line in lines)
        assert any("ANTHROPIC_API_KEY='api-key-123'" in line for line in lines)
        assert any("ANTHROPIC_AUTH_TOKEN='auth-token-456'" in line for line in lines)
        assert any("ANTHROPIC_DEFAULT_OPUS_MODEL='opus-test'" in line for line in lines)
        assert any("ANTHROPIC_DEFAULT_SONNET_MODEL='sonnet-test'" in line for line in lines)
        assert any("ANTHROPIC_DEFAULT_HAIKU_MODEL='haiku-test'" in line for line in lines)

    def test_export_special_characters_in_value(self, temp_config_dir, runner):
        """Test export handles special characters correctly."""
        # Test value with spaces
        runner.invoke(
            main,
            [
                "add",
                "special",
                "--description",
                "Test with space",
                "--opus-model",
                "model with space",
            ],
        )
        runner.invoke(main, ["select", "special"])

        result = runner.invoke(main, ["export"])
        assert result.exit_code == 0
        assert "model with space" in result.output


class TestConfigFileIntegration:
    """Test the ConfigFile class operations."""

    def test_get_active_model(self, temp_config_dir):
        """Test get_active() returns correct model."""
        config = ConfigFile(
            active="first",
            models={
                "first": ModelConfig(name="First"),
                "second": ModelConfig(name="Second"),
            },
        )
        active = config.get_active()
        assert active is not None
        assert active.name == "First"

    def test_get_active_nonexistent(self, temp_config_dir):
        """Test get_active() when active model doesn't exist."""
        config = ConfigFile(
            active="nonexistent",
            models={"first": ModelConfig(name="First")},
        )
        active = config.get_active()
        assert active is None

    def test_set_active(self, temp_config_dir):
        """Test set_active() changes active model."""
        config = ConfigFile(
            active="first",
            models={
                "first": ModelConfig(name="First"),
                "second": ModelConfig(name="Second"),
            },
        )
        result = config.set_active("second")
        assert result is True
        assert config.active == "second"

    def test_set_active_invalid(self, temp_config_dir):
        """Test set_active() with invalid model name."""
        config = ConfigFile(active="first", models={"first": ModelConfig()})
        result = config.set_active("nonexistent")
        assert result is False
        assert config.active == "first"

    def test_to_yaml_dict_full(self, temp_config_dir):
        """Test ConfigFile to_yaml_dict() output."""
        config = ConfigFile(
            active="local",
            models={
                "local": ModelConfig(
                    name="Local",
                    base_url="http://localhost",
                    opus_model="opus",
                ),
            },
        )
        data = config.to_yaml_dict()
        assert data["active"] == "local"
        assert "local" in data["models"]
        assert data["models"]["local"]["opus_model"] == "opus"


class TestEnvironmentVariableIsolation:
    """Test that environment variables work correctly in isolation."""

    def test_env_vars_only_from_model(self, temp_config_dir):
        """Test that only model-specific env vars are set."""
        model = ModelConfig(
            base_url="http://test.com",
            api_key="test-key",
            opus_model="test-model",
        )
        env = model.to_env_vars()

        assert "ANTHROPIC_BASE_URL" in env
        assert "ANTHROPIC_API_KEY" in env
        assert "ANTHROPIC_DEFAULT_OPUS_MODEL" in env

        # These should not be set because they weren't in the model
        assert "ANTHROPIC_AUTH_TOKEN" not in env
        assert "ANTHROPIC_DEFAULT_SONNET_MODEL" not in env

"""CLI interface for Claude Model Selector."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from .config import (
    add_model,
    ensure_config_dir,
    get_active_model,
    get_config_path,
    get_model,
    list_models,
    load_config,
    remove_model,
    set_active,
)
from .models import ModelConfig
from .selector import interactive_select


def interactive_add_fields(name, base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description):
    """
    Interactive prompts for add command with sensible defaults.

    Returns tuple of all field values (with defaults filled in for unanswered fields).
    Returns None if user cancels.
    """
    # Start with provided values
    if description is None:
        description = click.prompt("Description/Name for this model", default=name, show_default=True)

    # Suggest base URL based on whether it looks like a cloud or local deployment
    if base_url is None:
        cloud_suggestion = ""
        local_suggestion = "http://localhost:8080"

        # Check for common cloud patterns in the name
        name_lower = name.lower() if name else ""
        if any(x in name_lower for x in ["azure", "cloud", "aws", "gcp", "openai"]):
            cloud_suggestion = "https://api.anthropic.com"
            local_suggestion = ""

        if cloud_suggestion:
            base_url = click.prompt(
                "API base URL",
                default=cloud_suggestion,
                show_default=True,
            )
        elif local_suggestion:
            base_url = click.prompt(
                "API base URL",
                default=local_suggestion,
                show_default=True,
            )
        else:
            base_url = click.prompt(
                "API base URL (leave empty for default Anthropic)",
                default="",
                show_default=False,
            )

    # Ask for credentials based on whether there's a custom base URL
    if api_key is None and auth_token is None:
        if base_url and base_url != "":
            # Custom endpoint - try auth token first (OpenRouter, etc.)
            if click.prompt(
                "Will you use an auth token (e.g., OpenRouter) or API key?",
                type=click.Choice(["token", "key", "neither"]),
                default="token",
            ) == "token":
                auth_token = click.prompt(
                    "Authentication token",
                    hide_input=True,
                    default="",
                )
                if not auth_token:
                    click.echo("No auth token provided, leaving empty.")
            else:
                api_key = click.prompt(
                    "API key",
                    hide_input=True,
                    default="",
                )
                if not api_key:
                    click.echo("No API key provided, leaving empty.")
        else:
            # Default Anthropic endpoint - use API key
            api_key = click.prompt(
                "API key (for default Anthropic endpoint)",
                hide_input=True,
                default="",
            )
            if not api_key:
                click.confirm("Continue without API key?", default=False, abort=True)

    # Ask for model names if not provided
    if opus_model is None:
        opus_model = click.prompt(
            "Opus model name",
            default="claude-3-5-sonnet-20241022",
            show_default=True,
        )

    if sonnet_model is None:
        sonnet_model = click.prompt(
            "Sonnet model name",
            default="claude-3-5-sonnet-20241022",
            show_default=True,
        )

    if haiku_model is None:
        haiku_model = click.prompt(
            "Haiku model name",
            default="claude-3-haiku-20240307",
            show_default=True,
        )

    return base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Claude Model Selector - Manage Claude Code model configurations."""
    pass


@main.command()
def init():
    """Initialize configuration directory."""
    ensure_config_dir()
    config_path = get_config_path()
    click.echo(f"Configuration directory ready: {config_path.parent}")
    if not config_path.exists():
        click.echo(f"Create your first config with: {sys.argv[0]} add <name>")
    else:
        click.echo("Configuration file already exists.")


@main.command("list")
def list_models_cmd():
    """List all configured models."""
    models = list_models()
    active = get_active_model()

    if not models:
        click.echo("No models configured. Use 'add' to create one.")
        return

    # active is a ModelConfig object, we need the config to get the active name
    config = load_config()

    rows = []
    for name, model in sorted(models.items()):
        display_name = model.name or name
        active_marker = "<- ACTIVE" if name == config.active else ""
        rows.append((name, display_name, active_marker))

    col1 = max(len("Name"), max(len(r[0]) for r in rows))
    col2 = max(len("Name/Description"), max(len(r[1]) for r in rows))
    sep = col1 + col2 + 3 + len("<- ACTIVE")

    click.echo(f"{'Name':<{col1}}  {'Name/Description':<{col2}}  Active")
    click.echo("-" * sep)
    for name, display_name, active_marker in rows:
        click.echo(f"{name:<{col1}}  {display_name:<{col2}}  {active_marker}")


@main.command()
@click.argument("name", required=False)
@click.option("--base-url", default=None, help="API base URL")
@click.option("--api-key", default=None, help="API key")
@click.option("--auth-token", default=None, help="Authentication token")
@click.option("--opus-model", default=None, help="Opus model name")
@click.option("--sonnet-model", default=None, help="Sonnet model name")
@click.option("--haiku-model", default=None, help="Haiku model name")
@click.option("--description", "-d", default=None, help="Model description/name")
@click.option("-i", "--interactive", is_flag=True, help="Run interactive prompts for missing fields")
def add(name, base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description, interactive):
    """Add a new model configuration. Use -i for interactive prompts with sensible defaults."""
    if interactive:
        # Prompt for name first if not provided
        if not name:
            name = click.prompt("Model key/identifier (used in config)")
        # Re-check existence after name is known
        if get_model(name):
            click.echo(f"Model '{name}' already exists. Use 'edit' to modify it.")
            return
        base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description = interactive_add_fields(
            name, base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description
        )
    else:
        # Non-interactive mode: name is required
        if not name:
            click.echo("Error: Model name is required. Use 'add <name>' or 'add -i'.", err=True)
            sys.exit(1)
        if get_model(name):
            click.echo(f"Model '{name}' already exists. Use 'edit' to modify it.")
            return

    model = ModelConfig(
        name=description if description is not None else name,
        base_url=base_url or "",
        api_key=api_key or "",
        auth_token=auth_token or "",
        opus_model=opus_model or "",
        sonnet_model=sonnet_model or "",
        haiku_model=haiku_model or "",
    )
    add_model(name, model)
    click.echo(f"Added model configuration: {name}")


@main.command()
@click.argument("name")
@click.option("--base-url", help="New API base URL")
@click.option("--api-key", help="New API key")
@click.option("--auth-token", help="New authentication token")
@click.option("--opus-model", help="New Opus model name")
@click.option("--sonnet-model", help="New Sonnet model name")
@click.option("--haiku-model", help="New Haiku model name")
@click.option("--description", "-d", help="New model description/name")
def edit(name, base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description):
    """Edit an existing model configuration in your default text editor. Use options to update specific fields instead."""
    # Check if any options were provided
    has_options = any([base_url, api_key, auth_token, opus_model, sonnet_model, haiku_model, description is not None])

    if not has_options:
        # Open config file in default editor
        config_path = get_config_path()
        ensure_config_dir()
        editor_cmd = os.environ.get("EDITOR", "nano")
        click.echo(f"Opening {config_path} in {editor_cmd}...")
        try:
            result = subprocess.run([editor_cmd, str(config_path)])
            if result.returncode != 0:
                click.echo(f"Editor exited with code {result.returncode}.", err=True)
        except FileNotFoundError:
            fallback = "vi"
            click.echo(f"Editor '{editor_cmd}' not found, trying '{fallback}'...", err=True)
            try:
                subprocess.run([fallback, str(config_path)])
            except FileNotFoundError:
                click.echo(f"No editor found. Edit manually: {config_path}", err=True)
                return
        click.echo("Saved. Restart claude-code to apply changes.")
        return

    model = get_model(name)
    if not model:
        click.echo(f"Model '{name}' not found. Use 'list' to see available models.")
        return

    # Update only provided fields
    if description is not None:
        model.name = description
    if base_url is not None:
        model.base_url = base_url
    if api_key is not None:
        model.api_key = api_key
    if auth_token is not None:
        model.auth_token = auth_token
    if opus_model is not None:
        model.opus_model = opus_model
    if sonnet_model is not None:
        model.sonnet_model = sonnet_model
    if haiku_model is not None:
        model.haiku_model = haiku_model

    add_model(name, model)
    click.echo(f"Updated model configuration: {name}")


@main.command()
@click.argument("name")
def remove(name):
    """Remove a model configuration."""
    if not get_model(name):
        click.echo(f"Model '{name}' not found. Use 'list' to see available models.")
        return

    if click.confirm(f"Are you sure you want to remove model '{name}'?"):
        remove_model(name)
        click.echo(f"Removed model configuration: {name}")
    else:
        click.echo("Cancelled.")


@main.command()
@click.argument("name", required=False)
def select(name):
    """Select the active model configuration and run claude-code."""
    models = list_models()

    if not models:
        click.echo("No models configured. Use 'add' to create one first.")
        return

    if name:
        # Direct selection without auto-run
        if name not in models:
            click.echo(f"Model '{name}' not found. Use 'list' to see available models.")
            return
        set_active(name)
        model = get_model(name)
        click.echo(f"Activated model: {name}")
        if model and model.base_url:
            click.echo(f"  Base URL: {model.base_url}")
        return

    # Interactive selection
    interactive_select()


@main.command()
def show():
    """Show the currently active model configuration."""
    model = get_active_model()

    if not model:
        click.echo("No active model configured.")
        click.echo("Use 'select' to choose an active model.")
        return

    click.echo(f"Active Model: {model.name}")
    click.echo("")
    if model.base_url:
        click.echo(f"  Base URL:      {model.base_url}")
    if model.api_key:
        click.echo(f"  API Key:       {'*' * 8}")
    if model.auth_token:
        click.echo(f"  Auth Token:    {'*' * 8}")
    if model.opus_model:
        click.echo(f"  Opus Model:    {model.opus_model}")
    if model.sonnet_model:
        click.echo(f"  Sonnet Model:  {model.sonnet_model}")
    if model.haiku_model:
        click.echo(f"  Haiku Model:   {model.haiku_model}")


@main.command()
def export():
    """Output environment variables for the active model (for shell export)."""
    model = get_active_model()

    if not model:
        click.echo("No active model configured.", err=True)
        click.echo("Use 'select' to choose an active model first.", err=True)
        sys.exit(1)

    env_vars = model.to_env_vars()
    if not env_vars:
        click.echo("No environment variables set for this model.", err=True)
        sys.exit(1)

    for key, value in env_vars.items():
        click.echo(f"export {key}={model.escape_shell_value(value)}")


@main.command()
@click.argument("args", nargs=-1)
def run(args):
    """Run claude-code with a specific model or active model. Use 'run -- command' to run arbitrary commands."""
    if not args:
        # No args - use active model
        model = get_active_model()
        if not model:
            click.echo("Error: No active model configured. Use 'select <name>' to choose one first.", err=True)
            sys.exit(1)
        run_claude(model)
        return

    # Check if first arg is "--"
    if args[0] == "--":
        # Run arbitrary command with active model's environment
        active_model = get_active_model()
        if not active_model:
            click.echo("Error: No active model configured. Use 'select' to choose one first.", err=True)
            sys.exit(1)

        command = args[1:]
        if not command:
            click.echo("Error: No command provided after '--'.", err=True)
            sys.exit(1)

        run_command(active_model, command)
        return

    # First arg is model name
    name = args[0]
    model = get_model(name)
    if not model:
        click.echo(f"Model '{name}' not found. Use 'list' to see available models.", err=True)
        sys.exit(1)

    run_claude(model)


def _run_with_env(model, command: list[str]) -> None:
    """Run a command with a model's environment variables."""
    env_vars = model.to_env_vars()
    if not env_vars:
        click.echo("Error: No environment variables set for this model.", err=True)
        sys.exit(1)

    env = os.environ.copy()
    env.update(env_vars)

    try:
        subprocess.run(command, env=env, check=True)
    except FileNotFoundError:
        click.echo(f"Command not found: {command[0]}", err=True)
        sys.exit(127)
    except KeyboardInterrupt:
        pass


def _find_claude_exe() -> Optional[str]:
    """Find the claude executable in PATH."""
    return shutil.which("claude-code") or shutil.which("claude") or shutil.which("Claude")


def run_claude(model: ModelConfig, extra_args: tuple = ()) -> None:
    """Run claude-code with a model's environment."""
    claude_exe = _find_claude_exe()

    if not claude_exe:
        click.echo(
            "Error: Could not find claude-code or claude executable in PATH.",
            err=True,
        )
        click.echo(
            "Make sure Claude Code is installed and in your PATH.",
            err=True,
        )
        sys.exit(1)

    _run_with_env(model, [claude_exe, *extra_args])


def run_command(model: ModelConfig, command: list[str]) -> None:
    """Run an arbitrary command with a model's environment."""
    _run_with_env(model, command)


@main.command(
    name="claude",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def claude_cmd(args):
    """Run claude with the active model's environment, forwarding all arguments."""
    model = get_active_model()
    if not model:
        click.echo("Error: No active model configured. Use 'select <name>' to choose one first.", err=True)
        sys.exit(1)
    run_claude(model, extra_args=args)


@main.command()
def shell_init():
    """Generate shell integration script for auto-injecting environment variables."""
    config_path = get_config_path()
    script = f'''
# Claude Model Selector - Shell Integration
# Add this to your ~/.bashrc, ~/.zshrc, or similar

# Path to the configuration file
export CLAUDE_MODEL_CONFIG_PATH="{config_path}"

# Function to load environment variables from active model
claude-model-selector-load() {{
    if command -v python3 >/dev/null 2>&1; then
        $(python3 -m claude_model_selector export 2>/dev/null)
    else
        $(python -m claude_model_selector export 2>/dev/null)
    fi
}}

# Optional: Auto-load on shell start
# Uncomment the next line to auto-load:
# claude-model-selector-load

# Wrapper for claude-code that automatically loads config
claude() {{
    claude-model-selector-load
    command claude-code "$@"
}}

# Make claude-code use the wrapper alias
alias claude-code="claude"
'''
    click.echo(script.strip())


@main.command()
@click.argument("name", required=False)
def show_env(name):
    """Show environment variables for a model (or active model if no name provided)."""
    if name:
        model = get_model(name)
        if not model:
            click.echo(f"Model '{name}' not found. Use 'list' to see available models.")
            return
    else:
        model = get_active_model()
        if not model:
            click.echo("No active model configured. Use 'select <name>' to choose one first.")
            sys.exit(1)

    env_vars = model.to_env_vars()
    if not env_vars:
        click.echo(f"No environment variables set for this model.")
        return

    click.echo(f"Environment for model '{model.name}':")
    click.echo("")
    for key, value in env_vars.items():
        click.echo(f"  {key}={value}")


@main.command()
def update():
    """Update claude-model-selector to the latest version via uv."""
    click.echo("Updating claude-model-selector...")
    try:
        result = subprocess.run(
            ["uv", "tool", "upgrade", "claude-model-selector"],
            check=True,
        )
        click.echo("Update complete.")
    except FileNotFoundError:
        click.echo("Error: 'uv' not found. Install uv or reinstall manually:", err=True)
        click.echo("  uv tool install claude-model-selector", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        click.echo(f"Update failed (exit code {e.returncode}).", err=True)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()

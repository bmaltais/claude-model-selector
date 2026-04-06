"""Interactive model selection with fzf support."""

import subprocess
import sys
from typing import Optional

import click

from .config import list_models, set_active

# Timeout for fzf selection (seconds)
FZF_TIMEOUT = 30


def interactive_select() -> Optional[str]:
    """
    Interactive model selection.

    Uses fzf if available, otherwise falls back to simple numbered menu.
    Returns the selected model name or None if cancelled.
    """
    models = list_models()

    if not models:
        click.echo("No models configured. Use 'add' to create one first.")
        return None

    model_names = sorted(models.keys())

    # Try fzf first if available
    if can_use_fzf():
        return select_with_fzf(model_names)

    # Fall back to TUI menu
    return select_with_menu(model_names)


def can_use_fzf() -> bool:
    """Check if fzf is available in the shell."""
    try:
        result = subprocess.run(
            ["command", "-v", "fzf"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def select_with_fzf(model_names: list[str]) -> Optional[str]:
    """Select model using fzf."""
    # Create fzf prompt with model names
    prompt = "claude-model-selector-select"
    fzf_input = "\n".join([f"{name}|{name}" for name in model_names])

    try:
        result = subprocess.run(
            ["fzf", "--prompt", prompt, "--delimiter", "|", "--expect", "ctrl-t,ctrl-d,ctrl-c,enter"],
            input=fzf_input,
            capture_output=True,
            text=True,
            timeout=FZF_TIMEOUT,
        )

        if result.returncode != 0:
            # Ctrl-c or error - exit cleanly
            click.echo("Selection cancelled.")
            return None

        output = result.stdout.strip()
        if not output:
            return None

        parts = output.split("|", 1)
        selected = parts[1] if len(parts) > 1 else parts[0]

        return selected

    except subprocess.TimeoutExpired:
        click.echo("Selection timed out.")
        return None
    except FileNotFoundError:
        # fzf not found - fall back to menu
        pass
    except Exception as e:
        click.echo(f"Error with fzf: {e}", err=True)
        # Fall back to menu
        pass

    return select_with_menu(model_names)


def select_with_menu(model_names: list[str]) -> Optional[str]:
    """Select model using simple TUI menu."""
    click.echo("")
    click.echo("Available models:")
    click.echo("")

    models = list_models()
    for i, name in enumerate(model_names, 1):
        model = models[name]
        marker = " (active)" if model.name else ""
        click.echo(f"  {i}. {name}{marker}")

    click.echo("")
    click.echo(f"  0. Cancel")
    click.echo("")

    while True:
        try:
            choice = click.prompt(
                "Select model",
                type=click.IntRange(0, len(model_names)),
            )

            if choice == 0:
                click.echo("Cancelled.")
                return None

            selected = model_names[choice - 1]

            if set_active(selected):
                model = models[selected]
                click.echo(f"Activated model: {selected}")
                if model and model.base_url:
                    click.echo(f"  Base URL: {model.base_url}")
                return selected
            else:
                click.echo(f"Error: Could not activate {selected}")

        except KeyboardInterrupt:
            click.echo("")
            click.echo("Cancelled.")
            return None

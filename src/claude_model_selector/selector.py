"""Interactive model selection."""

from typing import Optional

import click
import questionary
from questionary import Choice

from .config import list_models, load_config, set_active


def interactive_select() -> Optional[str]:
    """
    Interactive model selection using arrow-key TUI.

    Returns the selected model name or None if cancelled.
    """
    models = list_models()

    if not models:
        click.echo("No models configured. Use 'add' to create one first.")
        return None

    config = load_config()
    model_names = sorted(models.keys())

    choices = []
    for name in model_names:
        model = models[name]
        description = model.name if model.name and model.name != name else ""
        base_url = model.base_url or "default Anthropic"
        subtitle = f"{description} — {base_url}" if description else base_url
        choices.append(Choice(title=f"{name}  ({subtitle})", value=name))

    try:
        selected = questionary.select(
            "Select a model:",
            choices=choices,
            default=next(
                (c for c in choices if c.value == config.active), choices[0]
            ) if config.active else choices[0],
            use_shortcuts=False,
            style=questionary.Style([
                ("highlighted", "bold fg:cyan"),
                ("pointer", "bold fg:cyan"),
                ("selected", "bold"),
            ]),
        ).ask()
    except KeyboardInterrupt:
        click.echo("\nCancelled.")
        return None

    if selected is None:
        click.echo("Cancelled.")
        return None

    if set_active(selected):
        model = models[selected]
        click.echo(f"Activated: {selected}")
        if model and model.base_url:
            click.echo(f"  Base URL: {model.base_url}")
    else:
        click.echo(f"Error: Could not activate {selected}", err=True)

    return selected

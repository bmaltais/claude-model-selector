# Claude Model Selector

<div align="center">

**Seamlessly switch between Claude model configurations and endpoints**

[![PyPI version](https://badge.fury.io/py/claude-model-selector.svg)](https://badge.fury.io/py/claude-model-selector)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

Manage Claude Code model configurations and environment variables. Easily switch between different model endpoints (local, remote, production) without manually managing environment variables.

## Features

- **Switch models instantly** - Change between local development, staging, and production Claude endpoints
- **Environment management** - Automatic export of required environment variables
- **Interactive selection** - Use `fzf` for fuzzy search or numbered menus
- **Shell integration** - Seamless integration with your shell profile
- **Editor support** - Edit configurations in your default text editor
- **Configurable** - Supports custom config file paths

## Installation

```bash
# Using uv (recommended)
uv tool install --from . claude-model-selector

# or using pip
pip install .
```

> **Note:** After installing with `uv tool install` for the first time, the tool's bin directory is added to your PATH — but this change only takes effect in **new terminal sessions**. If `claude-model-selector` is not found immediately after installing, open a new terminal (or reload your shell profile) and try again.
>
> **Windows (PowerShell):** Open a new PowerShell or Command Prompt window.
>
> **macOS / Linux:** Open a new terminal, or run:
> ```bash
> source ~/.zshrc    # zsh (macOS default)
> source ~/.bashrc   # bash
> ```

### Updating

```bash
# Self-update via the CLI (requires uv)
claude-model-selector update

# Or manually:
uv tool upgrade claude-model-selector
```

### Reinstalling from source

```bash
uv tool install --from . claude-model-selector --force
```

## Quick Start

```bash
# Initialize configuration storage
claude-model-selector init

# Add a model configuration
claude-model-selector add my-local \
  --base-url http://localhost:8000 \
  --api-key mykey \
  --opus-model qwen3.5-35b

# Select a model (automatically starts claude-code)
claude-model-selector select my-local
```

## Usage

### Command Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize configuration directory |
| `list` | List all configured models |
| `add [name] -i` | Add a new model configuration (use `-i` for interactive mode) |
| `edit <name>` | Edit an existing model in your default editor |
| `remove <name>` | Remove a model configuration |
| `select [name]` | Select model and run claude-code (interactive without name) |
| `show` | Show the currently active model |
| `export` | Output environment variables (for `export $(...)`) |
| `run <name>` | Run claude-code with a specific model |
| `shell-init` | Generate shell integration script |
| `show-env <name>` | Show environment variables for a model |
| `update` | Update to the latest version via uv |

### Adding Models

**Interactive mode (recommended):**
```bash
claude-model-selector add -i
# Prompts for name, base URL, credentials, and model names with sensible defaults
```

**Command line:**
```bash
claude-model-selector add my-local \
  --base-url http://localhost:8000 \
  --api-key mykey \
  --opus-model qwen3.5-35b
```

### Editing Models

**Open in editor:**
```bash
claude-model-selector edit qwen3.5-35b
# Opens ~/.claude/model-config/models.yaml in $EDITOR (or nano)
```

**Update specific fields:**
```bash
claude-model-selector edit qwen3.5-35b --base-url http://new-url:8000
```

### Selecting and Running Models

```bash
# Select and run claude-code immediately
claude-model-selector select qwen3.5-35b

# Interactive selection (uses fzf if available)
claude-model-selector select

# Run with a specific model (without selecting)
claude-model-selector run qwen3.5-35b
```

### Shell Integration

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
claude-model-selector shell-init >> ~/.bashrc
source ~/.bashrc
```

Now you can:
- `claude-model-selector select <name>` - Switch models
- `claude-code` - Automatically uses the active model's environment

### Interactive Selection

Run `claude-model-selector select` without arguments for interactive mode:
- Uses **fzf** if available for fuzzy search
- Falls back to numbered menu otherwise

## Configuration

### Config File Format

Models are stored in `~/.claude/model-config/models.yaml`:

```yaml
active: my-local
models:
  my-local:
    name: Local Development
    base_url: http://localhost:8000
    api_key: dummy
    opus_model: qwen3.5-35b
    sonnet_model: qwen3.5-35b
    haiku_model: qwen3.5-35b

  remote:
    name: Production
    base_url: https://api.anthropic.com
    api_key: ${ANTHROPIC_API_KEY}
```

### Environment Variables

The following are exported based on your model config:

- `ANTHROPIC_BASE_URL` - API endpoint
- `ANTHROPIC_API_KEY` - API key
- `ANTHROPIC_AUTH_TOKEN` - Auth token
- `ANTHROPIC_DEFAULT_OPUS_MODEL` - Opus model name
- `ANTHROPIC_DEFAULT_SONNET_MODEL` - Sonnet model name
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` - Haiku model name

### Custom Config Path

Use `CLAUDE_MODEL_CONFIG_PATH` environment variable to use a custom config file:

```bash
export CLAUDE_MODEL_CONFIG_PATH=/path/to/my/models.yaml
claude-model-selector select my-model
```

## Development

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install in development mode
uv sync

# Run the CLI
uv run claude-model-selector --help

# Run tests
uv run pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

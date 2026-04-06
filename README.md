# Claude Model Selector

Manage Claude Code model configurations and environment variables. Easily switch between different model endpoints (local, remote, production) without manually managing environment variables.

## Installation

```bash
uv tool install --from . claude-model-selector
# or
pip install .
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

### Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize configuration directory |
| `list` | List all configured models |
| `add [name] -i` | Add a new model configuration (use `-i` for interactive prompts with defaults) |
| `edit <name>` | Edit an existing model configuration in your default text editor |
| `remove <name>` | Remove a model configuration |
| `select [name]` | Select the active model and run claude-code (interactive without name) |
| `show` | Show the currently active model |
| `export` | Output environment variables (for `export $(...)`) |
| `run <name>` | Run claude-code with a specific model |
| `shell-init` | Generate shell integration script |
| `show-env <name>` | Show env vars for a specific model |

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

### Selecting Models

```bash
# Select and run claude-code immediately
claude-model-selector select qwen3.5-35b

# Interactive selection (uses fzf if available)
claude-model-selector select
```

### Running Claude with Specific Models

```bash
# Run claude-code with a specific model
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

## Environment Variables

The following are exported based on your model config:

- `ANTHROPIC_BASE_URL` - API endpoint
- `ANTHROPIC_API_KEY` - API key
- `ANTHROPIC_AUTH_TOKEN` - Auth token
- `ANTHROPIC_DEFAULT_OPUS_MODEL` - Opus model name
- `ANTHROPIC_DEFAULT_SONNET_MODEL` - Sonnet model name
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` - Haiku model name

## Custom Config Path

Use `CLAUDE_MODEL_CONFIG_PATH` environment variable to use a custom config file:

```bash
export CLAUDE_MODEL_CONFIG_PATH=/path/to/my/models.yaml
claude-model-selector select my-model
```

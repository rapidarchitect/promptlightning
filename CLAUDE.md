
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PromptVault is a Python library for managing and rendering prompt templates with type-safe inputs, versioning, and optional logging. The architecture consists of:

- **Vault**: Main public API (`promptvault/vault.py`) - loads templates, handles caching with thread-safe RLock, and provides TemplateHandle objects
- **Registry**: Template discovery system (`promptvault/registry/`) - abstract base with LocalRegistry implementation that scans YAML files in prompt directories
- **Model**: Pydantic-based template specifications (`promptvault/model.py`) - defines TemplateSpec with input validation and type coercion
- **Renderer**: Jinja2-based template rendering (`promptvault/renderer.py`) - includes custom filters like `yaml` and `default`
- **CLI**: Typer-based command interface (`promptvault/cli.py`) - provides init, list, get, bump, and watch commands

Templates are stored as YAML files with structure: `{id, version, description, template, inputs, metadata}`. The `inputs` field defines typed parameters (string, number, boolean, array<string>, object) with validation and defaults.

## Development Commands

**Environment Setup:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
export PATH="$HOME/.local/bin:$PATH" && uv sync

# Run CLI commands during development
export PATH="$HOME/.local/bin:$PATH" && uv run python -m promptvault.cli --help
```

**Testing the CLI:**
```bash
# Initialize a test project
export PATH="$HOME/.local/bin:$PATH" && uv run python -m promptvault.cli init

# List templates
export PATH="$HOME/.local/bin:$PATH" && uv run python -m promptvault.cli list

# Get template content
export PATH="$HOME/.local/bin:$PATH" && uv run python -m promptvault.cli get summarizer

# Watch for changes
export PATH="$HOME/.local/bin:$PATH" && uv run python -m promptvault.cli watch
```

**Library Usage:**
```bash
# Test vault functionality
export PATH="$HOME/.local/bin:$PATH" && uv run python -c "
from promptvault.vault import Vault
v = Vault(prompt_dir='./prompts')
tmpl = v.get('summarizer')
print(tmpl.render(input_text='test'))
"
```

## Key Architecture Notes

- Thread-safe caching in Vault class using RLock for concurrent access
- Registry pattern allows future extension beyond local filesystem (e.g., remote registries)
- TemplateHandle separates template metadata from rendering concerns
- Input validation happens at render time via Pydantic with custom type coercion
- Jinja2 environment configured with StrictUndefined to catch template errors early
- File watching uses separate Watcher class for hot-reload functionality

## Configuration

Projects use `promptvault.yaml` config files with structure:
```yaml
registry: "local"
prompt_dir: "./prompts"
logging:
  enabled: true
  backend: "sqlite"
  db_path: "./promptvault.db"
```

## Code Style Guidelines

- **No emoticons**: Never use emoticons or emojis in code, commit messages, or any generated content
- **Minimal comments**: Avoid code comments unless absolutely necessary for complex logic or non-obvious behavior
- **Assume expertise**: Write code assuming prior software engineering knowledge - avoid explanatory comments for standard patterns
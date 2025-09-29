
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dakora is a Python library for managing and rendering prompt templates with type-safe inputs, versioning, and optional logging. The architecture consists of:

- **Vault**: Main public API (`dakora/vault.py`) - loads templates, handles caching with thread-safe RLock, and provides TemplateHandle objects
- **Registry**: Template discovery system (`dakora/registry/`) - abstract base with LocalRegistry implementation that scans YAML files in prompt directories
- **Model**: Pydantic-based template specifications (`dakora/model.py`) - defines TemplateSpec with input validation and type coercion
- **Renderer**: Jinja2-based template rendering (`dakora/renderer.py`) - includes custom filters like `yaml` and `default`
- **CLI**: Typer-based command interface (`dakora/cli.py`) - provides init, list, get, bump, watch, and playground commands
- **Playground**: FastAPI-based web server (`dakora/playground.py`) - interactive web interface for template development and testing

Templates are stored as YAML files with structure: `{id, version, description, template, inputs, metadata}`. The `inputs` field defines typed parameters (string, number, boolean, array<string>, object) with validation and defaults.

## Development Commands

**Environment Setup:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
export PATH="$HOME/.local/bin:$PATH" && uv sync

# Run CLI commands during development
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli --help
```

**Testing the CLI:**
```bash
# Initialize a test project
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli init

# List templates
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli list

# Get template content
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli get summarizer

# Watch for changes
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli watch
```

**Testing the Playground:**
```bash
# Start interactive playground web interface
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli playground --port 3000

# Start in development mode with auto-reload
export PATH="$HOME/.local/bin:$PATH" && uv run python -m dakora.cli playground --dev
```

**Library Usage:**
```bash
# Test vault functionality
export PATH="$HOME/.local/bin:$PATH" && uv run python -c "
from dakora.vault import Vault
v = Vault(prompt_dir='./prompts')
tmpl = v.get('summarizer')
print(tmpl.render(input_text='test'))
"
```

**Running Tests:**
```bash
# Run all tests
export PATH="$HOME/.local/bin:$PATH" && uv run python -m pytest

# Run specific test categories
export PATH="$HOME/.local/bin:$PATH" && uv run python tests/test_runner.py unit
export PATH="$HOME/.local/bin:$PATH" && uv run python tests/test_runner.py integration
export PATH="$HOME/.local/bin:$PATH" && uv run python tests/test_runner.py performance

# Quick validation test
python validate_tests.py

# Run tests with coverage
export PATH="$HOME/.local/bin:$PATH" && uv run python -m pytest --cov=dakora
```

## Key Architecture Notes

- Thread-safe caching in Vault class using RLock for concurrent access
- Registry pattern allows future extension beyond local filesystem (e.g., remote registries)
- TemplateHandle separates template metadata from rendering concerns
- Input validation happens at render time via Pydantic with custom type coercion
- Jinja2 environment configured with StrictUndefined to catch template errors early
- File watching uses separate Watcher class for hot-reload functionality

## Configuration

Projects use `dakora.yaml` config files with structure:
```yaml
registry: "local"
prompt_dir: "./prompts"
logging:
  enabled: true
  backend: "sqlite"
  db_path: "./dakora.db"
```

## Code Style Guidelines

- **No emoticons**: Never use emoticons or emojis in code, commit messages, or any generated content
- **Minimal comments**: Avoid code comments unless absolutely necessary for complex logic or non-obvious behavior
- **Assume expertise**: Write code assuming prior software engineering knowledge - avoid explanatory comments for standard patterns
- memory plan to build the opensource project
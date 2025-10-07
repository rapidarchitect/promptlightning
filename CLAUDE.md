
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PromptLightning is a Python library for managing and executing LLM prompt templates with type-safe inputs, versioning, and optional logging. The architecture consists of:

- **Vault**: Main public API (`promptlightning/vault.py`) - loads templates, handles caching with thread-safe RLock, and provides TemplateHandle objects
- **Registry**: Template discovery system (`promptlightning/registry/`) - abstract base with LocalRegistry implementation that scans YAML files in prompt directories
- **Model**: Pydantic-based template specifications (`promptlightning/model.py`) - defines TemplateSpec with input validation and type coercion
- **Renderer**: Jinja2-based template rendering (`promptlightning/renderer.py`) - includes custom filters like `yaml` and `default`
- **CLI**: Typer-based command interface (`promptlightning/cli.py`) - provides init, list, get, bump, watch, run, and playground commands
- **Playground**: FastAPI-based web server (`promptlightning/playground.py`) - interactive React-based web interface for template development and testing, with demo mode support
- **LLM Client**: LiteLLM integration (`promptlightning/llm/client.py`) - executes templates against 100+ LLM providers with cost tracking
- **Logging**: Optional SQLite-based execution logging (`promptlightning/logging.py`) - tracks template executions with inputs, outputs, and metadata
- **Watcher**: File system monitoring (`promptlightning/watcher.py`) - hot-reload support for template changes during development
- **Exceptions**: Custom exception hierarchy (`promptlightning/exceptions.py`) - PromptLightningError, TemplateNotFoundError, ValidationError, LLMError subtypes (APIKeyError, RateLimitError, ModelNotFoundError)

Templates are stored as YAML files with structure: `{id, version, description, template, inputs, metadata}`. The `inputs` field defines typed parameters (string, number, boolean, array<string>, object) with validation and defaults.

The playground UI is built with React, TypeScript, Vite, and shadcn/ui components, providing a modern interface for template development. It supports both development mode (hot-reload) and demo mode (read-only with example templates).

## Development Commands

**Environment Setup:**
```bash
# Clone and setup
git clone https://github.com/bogdan-pistol/promptlightning.git
cd promptlightning
uv sync
source .venv/bin/activate
```

**Running the CLI (Development):**
```bash
# All CLI commands use uv run during development
uv run python -m promptlightning.cli --help

# Initialize project
uv run python -m promptlightning.cli init

# List templates
uv run python -m promptlightning.cli list

# Get template content
uv run python -m promptlightning.cli get summarizer

# Bump template version
uv run python -m promptlightning.cli bump summarizer --minor

# Watch for changes
uv run python -m promptlightning.cli watch
```

**LLM Execution:**
```bash
# Execute template with LLM (requires API keys in .env)
uv run python -m promptlightning.cli run summarizer --model gpt-4 --input-text "Article content..."

# With additional LLM parameters
uv run python -m promptlightning.cli run summarizer --model gpt-4 --input-text "Text..." --temperature 0.7 --max-tokens 100

# JSON output for scripting
uv run python -m promptlightning.cli run summarizer --model gpt-4 --input-text "Text..." --json

# Quiet mode (only LLM response)
uv run python -m promptlightning.cli run summarizer --model gpt-4 --input-text "Text..." --quiet
```

**Playground:**
```bash
# Start playground (builds UI automatically on first run)
uv run python -m promptlightning.cli playground

# Development mode with hot-reload
uv run python -m promptlightning.cli playground --dev

# Demo mode (read-only with examples)
uv run python -m promptlightning.cli playground --demo

# Custom port
uv run python -m promptlightning.cli playground --port 8080

# Skip UI build / don't open browser
uv run python -m promptlightning.cli playground --no-build --no-browser
```

**Testing:**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=promptlightning

# Run specific test file
uv run pytest tests/test_vault_execute.py

# Run smoke tests
uv run python tests/smoke_test.py

# Run test categories
uv run python tests/test_runner.py unit
uv run python tests/test_runner.py integration
uv run python tests/test_runner.py performance
```

**Code Quality:**
```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy promptlightning
```

**Library Usage (Development):**
```bash
# Test vault functionality
uv run python -c "
from promptlightning.vault import Vault
v = Vault(prompt_dir='./prompts')
tmpl = v.get('summarizer')
print(tmpl.render(input_text='test'))
"

# Test LLM execution
uv run python -c "
from promptlightning.vault import Vault
v = Vault('promptlightning.yaml')
result = v.get('summarizer').execute(model='gpt-4', input_text='Test article')
print(f'Output: {result.output}')
print(f'Cost: \${result.cost_usd:.4f}')
"
```

## Key Architecture Notes

- **Thread-safe caching**: Vault class uses RLock for concurrent access to template cache
- **Registry pattern**: Abstract base allows future extension beyond local filesystem (e.g., remote registries)
- **TemplateHandle separation**: Template metadata separated from rendering concerns for cleaner API
- **Input validation**: Happens at render/execute time via Pydantic with custom type coercion logic
- **Jinja2 configuration**: StrictUndefined mode to catch template errors early
- **File watching**: Separate Watcher class for hot-reload via `invalidate_cache()` callback
- **Playground architecture**: FastAPI backend with CORS, static file serving, and automatic UI build from `web/` source
- **UI build process**: Vite + React + TypeScript in `web/` directory, builds to `playground/` directory
- **Demo mode**: Serves example templates from embedded YAML, read-only interface
- **LLM integration**: LiteLLM client with unified interface for 100+ providers, automatic cost/token tracking
- **Execution flow**: `execute()` method separates template inputs from LLM parameters, renders prompt, calls LLM, logs results
- **Logging backend**: SQLite storage with timestamps, inputs, outputs, latency, cost, and provider metadata

## Template Structure

Templates are YAML files with this structure:
```yaml
id: unique_template_id          # Required: Template identifier
version: 1.0.0                  # Required: Semantic version
description: Template purpose   # Optional: Human-readable description
template: |                     # Required: Jinja2 template string
  Your template content here
  {{ variable_name }}
inputs:                         # Optional: Input specifications
  variable_name:
    type: string                # string|number|boolean|array<string>|object
    required: true              # Default: true
    default: "default value"    # Optional: Default value
metadata:                       # Optional: Custom metadata
  tags: ["tag1", "tag2"]
  author: "Your Name"
```

## Configuration

`promptlightning.yaml` structure:
```yaml
registry: local                 # Registry type (currently only 'local')
prompt_dir: ./prompts          # Path to templates directory
logging:                       # Optional: Execution logging
  enabled: true
  backend: sqlite
  db_path: ./promptlightning.db
```

## Code Style Guidelines

- **No emoticons**: Never use emoticons or emojis in code, commit messages, or any generated content
- **Minimal comments**: Avoid code comments unless absolutely necessary for complex logic or non-obvious behavior
- **Assume expertise**: Write code assuming prior software engineering knowledge - avoid explanatory comments for standard patterns
- **Type hints**: Use Python type hints throughout the codebase for better IDE support
- **Error handling**: Use custom exception hierarchy for clear error messages
- **Testing**: Maintain test coverage with unit, integration, and performance tests

## Project Structure

```
promptlightning/
├── promptlightning/
│   ├── __init__.py          # Public API exports (Vault)
│   ├── vault.py             # Vault and TemplateHandle classes
│   ├── model.py             # Pydantic models (TemplateSpec, InputSpec)
│   ├── renderer.py          # Jinja2 rendering engine
│   ├── cli.py               # Typer-based CLI (init, list, get, run, playground, bump, watch)
│   ├── playground.py        # FastAPI web server
│   ├── logging.py           # SQLite logging backend
│   ├── watcher.py           # File system monitoring
│   ├── exceptions.py        # Custom exception hierarchy
│   ├── types.py             # Type definitions
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py        # LiteLLM integration
│   │   └── models.py        # ExecutionResult model
│   └── registry/
│       ├── base.py          # Abstract registry interface
│       └── local.py         # Local filesystem registry
├── web/                     # React + TypeScript source (Vite)
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities and API client
│   │   └── App.tsx          # Main application
│   ├── package.json
│   └── vite.config.ts
├── playground/              # Built UI (generated from web/)
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_vault_execute.py   # LLM execution tests
│   ├── test_llm_client.py      # LLM client tests
│   ├── test_playground_*.py    # Playground API/server tests
│   └── test_runner.py          # Test category runner
├── prompts/                 # Example templates
└── pyproject.toml           # Project metadata
```

# PromptLightning

<p align="center">
  <img src="docs/assets/logo.svg" alt="PromptLightning Logo" width="200">
</p>

[![CI](https://github.com/bogdan-pistol/promptlightning/workflows/CI/badge.svg)](https://github.com/bogdan-pistol/promptlightning/actions)
[![codecov](https://codecov.io/gh/bogdan-pistol/promptlightning/branch/main/graph/badge.svg)](https://codecov.io/gh/bogdan-pistol/promptlightning)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/promptlightning.svg)](https://badge.fury.io/py/promptlightning)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Discord](https://img.shields.io/discord/1422246380096720969?style=for-the-badge&color=667eea&label=Community&logo=discord&logoColor=white)](https://discord.gg/QSRRcFjzE8)

A Python library for managing and executing LLM prompts with type-safe inputs, versioning, and an interactive web playground. Execute templates against 100+ LLM providers with built-in cost tracking.

## 🚀 Try it Now - No Installation Required!

**[playground.promptlightning.io](https://playground.promptlightning.io/)** - Experience PromptLightning's interactive playground directly in your browser. Edit templates, test inputs, and see instant results with the exact same interface that ships with the Python package.

## Use Case

```python
from promptlightning import Vault

# Load your templates
vault = Vault("promptlightning.yaml")

# Execute against any LLM provider
result = vault.get("summarizer").execute(
    model="gpt-4",
    input_text="Your article here..."
)

print(result.output)          # The LLM's response
print(f"${result.cost_usd}")  # Track costs automatically
```

Or from the command line:

```bash
promptlightning run summarizer --model gpt-4 --input-text "Article..."
```

## Features

- 🌐 **[Live Web Playground](https://playground.promptlightning.io/)** - Try online without installing anything!
- 🎯 **Local Playground** - Same modern React UI included with pip install
- 🚀 **LLM Execution** - Run templates against 100+ LLM providers (OpenAI, Anthropic, Google, etc.)
- ⚡ **Lightning-Fast Storage** - LMDB-powered registry with 450-4,380x performance improvement
- 🎨 **Type-safe prompt templates** with validation and coercion
- 📁 **File-based template management** with YAML definitions
- 🔄 **Hot-reload support** for development
- 📝 **Jinja2 templating** with custom filters
- 🏷️ **Semantic versioning** for templates
- 📊 **Optional execution logging** to SQLite with cost tracking
- 🖥️ **CLI interface** for template management and execution
- 🧵 **Thread-safe caching** for production use
- 💰 **Cost & performance tracking** - Monitor tokens, latency, and costs

## Performance

PromptLightning uses LMDB (Lightning Memory-Mapped Database) for ultra-fast template storage:

- **450-4,380x faster** than YAML file scanning
- **O(1) constant-time lookups** via memory mapping
- **Zero-copy reads** for maximum efficiency
- **Thread-safe** concurrent access
- **Production-ready** ACID-compliant storage

### Performance Comparison

| Operation | YAML Registry | LMDB Registry | Speedup |
|-----------|--------------|---------------|---------|
| Load 10 templates (50 lookups) | 86ms | 0.2ms | 451x |
| Load 50 templates (200 lookups) | 1,595ms | 0.7ms | 2,275x |
| Load 100 templates (500 lookups) | 7,817ms | 1.8ms | 4,380x |

See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for detailed benchmarks.

## Migration from YAML

Upgrading from YAML-based storage? Migrate with one command:

```bash
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb
```

The migration tool:
- Automatically converts all YAML templates to LMDB
- Verifies data integrity after migration
- Preserves all template metadata and versioning
- Provides detailed migration report

See [MIGRATION.md](MIGRATION.md) for the complete migration guide.

## Installation

```bash
pip install promptlightning
```

**For the interactive playground**:
- PyPI releases include a pre-built UI - just run `promptlightning playground`
- For development installs (git clone), Node.js 18+ is required
- The UI builds automatically from source on first run if not present

Or for development:

```bash
git clone https://github.com/bogdan-pistol/promptlightning.git
cd promptlightning
uv sync
source .venv/bin/activate
```

## Quick Start

### 1. Initialize a project

```bash
promptlightning init
```

This creates:
- `promptlightning.yaml` - Configuration file
- `prompts/` - Directory for template files
- `prompts/summarizer.yaml` - Example template

### 2. Create a template

Create `prompts/greeting.yaml`:

```yaml
id: greeting
version: 1.0.0
description: A personalized greeting template
template: |
  Hello {{ name }}!
  {% if age %}You are {{ age }} years old.{% endif %}
  {{ message | default("Have a great day!") }}
inputs:
  name:
    type: string
    required: true
  age:
    type: number
    required: false
  message:
    type: string
    required: false
    default: "Welcome to PromptLightning!"
```

### 3. Use in Python

```python
from promptlightning import Vault

# Initialize vault
vault = Vault("promptlightning.yaml")

# Get and render template
template = vault.get("greeting")
result = template.render(name="Alice", age=25)
print(result)
# Output:
# Hello Alice!
# You are 25 years old.
# Welcome to PromptLightning!
```

### 4. Interactive Playground 🎯

#### Try Online - No Installation Required!
Visit **[playground.promptlightning.io](https://playground.promptlightning.io/)** to experience the playground instantly in your browser with example templates.

#### Or Run Locally
Launch the same web-based playground locally (included with pip install):

```bash
promptlightning playground
```

![Playground Demo](docs/assets/playground-demo.gif)

This **automatically**:
- 🔨 Builds the modern React UI (first run only)
- 🚀 Starts the server at `http://localhost:3000`
- 🌐 Opens your browser to the playground

**Features:**
- ✨ **Identical experience** online and locally
- 📱 Mobile-friendly design that works on all screen sizes
- 🎨 Real-time template editing and preview
- 🧪 Test templates with different inputs
- 📊 Example templates for inspiration
- 💻 Modern UI built with shadcn/ui components

![Playground Interface](docs/assets/playground-interface.png)

**Local Options:**
```bash
promptlightning playground --port 8080      # Custom port
promptlightning playground --no-browser     # Don't open browser
promptlightning playground --no-build       # Skip UI build
promptlightning playground --demo           # Run in demo mode (like the web version)
```

### 5. Execute Templates with LLMs

PromptLightning can execute templates against real LLM providers (OpenAI, Anthropic, Google, etc.) using the integrated LiteLLM support.

#### API Key Setup

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export GOOGLE_API_KEY=your_key_here
```

Or create a `.env` file in your project root:

```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

**Security Note:** Never commit API keys to version control. Add `.env` to your `.gitignore`.

#### Execute from Python

```python
from promptlightning import Vault

vault = Vault("promptlightning.yaml")
template = vault.get("summarizer")

# Execute with gpt-4
result = template.execute(
    model="gpt-4",
    input_text="Your article content here..."
)

print(result.output)
print(f"Cost: ${result.cost_usd:.4f}")
print(f"Tokens: {result.tokens_in} → {result.tokens_out}")
```

#### Execute from CLI

```bash
# Basic execution
promptlightning run summarizer --model gpt-4 --input-text "Article to summarize..."

# With LLM parameters
promptlightning run summarizer --model gpt-4 \
  --input-text "Article..." \
  --temperature 0.7 \
  --max-tokens 100

# JSON output for scripting
promptlightning run summarizer --model gpt-4 \
  --input-text "Article..." \
  --json

# Quiet mode (only LLM response)
promptlightning run summarizer --model gpt-4 \
  --input-text "Article..." \
  --quiet
```

**Example Output:**

```
╭─────────────────────────────────────╮
│ Model: gpt-4 (openai)               │
│ Cost: $0.0045 USD                   │
│ Latency: 1,234 ms                   │
│ Tokens: 150 → 80                    │
╰─────────────────────────────────────╯

The article discusses the recent advances in...
```

#### Supported Models

PromptLightning supports 100+ LLM providers through LiteLLM:

- **OpenAI:** `gpt-4`, `gpt-4-turbo`, `gpt-5-nano`, `gpt-3.5-turbo`
- **Anthropic:** `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- **Google:** `gemini-pro`, `gemini-1.5-pro`
- **Local:** `ollama/llama3`, `ollama/mistral`
- **And many more...**

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for the full list.

### 6. CLI Usage

![CLI Workflow](docs/assets/cli-workflow.gif)

```bash
# List all templates
promptlightning list

# Get template content
promptlightning get greeting

# Execute a template
promptlightning run summarizer --model gpt-4 --input-text "..."

# Bump version
promptlightning bump greeting --minor

# Watch for changes
promptlightning watch
```

![CLI Output](docs/assets/cli-output.png)

## Template Format

Templates are defined in YAML files with the following structure:

![Template Editing](docs/assets/template-editing.png)

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

### Supported Input Types

- `string` - Text values
- `number` - Numeric values (int/float)
- `boolean` - True/false values
- `array<string>` - List of strings
- `object` - Dictionary/JSON object

### Built-in Jinja2 Filters

- `default(value)` - Provide fallback for empty values
- `yaml` - Convert objects to YAML format

## Configuration

`promptlightning.yaml` structure:

```yaml
# LMDB registry (recommended for production)
registry: lmdb
db_path: ./templates.lmdb
logging:
  enabled: true
  backend: sqlite
  db_path: ./promptlightning.db

# Legacy YAML registry (still supported)
# registry: local
# prompt_dir: ./prompts
```

**LMDB Registry** (Recommended):
- 450-4,380x faster than YAML file scanning
- O(1) constant-time lookups
- Production-ready ACID storage
- Ideal for applications with many templates

**Local Registry** (Development):
- Human-readable YAML files
- Easy to edit and version control
- Good for small template collections
- Simple development workflow

## Advanced Usage

### FastAPI + OpenAI Integration

PromptLightning works great with web APIs. Here's a FastAPI example using OpenAI's latest Responses API and GPT-5:

```python
from fastapi import FastAPI
from promptlightning import Vault
from openai import OpenAI

app = FastAPI()
vault = Vault("promptlightning.yaml")
client = OpenAI()

@app.post("/chat")
async def chat_endpoint(message: str, template_id: str):
    template = vault.get(template_id)

    # Use template's run method with new Responses API
    result = template.run(
        lambda prompt: client.responses.create(
            model="gpt-5",
            reasoning={"effort": "medium"},
            input=prompt
        ).output_text,
        message=message
    )

    return {"response": result}
```

## Examples

### Multi-Agent Research Assistant

**[examples/openai-agents/](examples/openai-agents/)** - Build intelligent research agents with the OpenAI Agents Framework, using PromptLightning to manage complex multi-agent prompts with type-safe inputs and hot-reload during development.

### FastAPI Integration

See [examples/fastapi/](examples/fastapi/) for a complete FastAPI application with multiple endpoints, reasoning controls, and error handling.

### With Logging

```python
from promptlightning import Vault

vault = Vault("promptlightning.yaml")
template = vault.get("my_template")

# Log execution automatically
result = template.run(
    lambda prompt: call_your_llm(prompt),
    input_text="Hello world"
)
```

### Direct Vault Creation

```python
from promptlightning import Vault

# Skip config file, use prompt directory directly
vault = Vault(prompt_dir="./my_prompts")
```

### Hot Reload in Development

```python
from promptlightning import Vault
from promptlightning.watcher import Watcher

vault = Vault("promptlightning.yaml")
watcher = Watcher("./prompts", on_change=vault.invalidate_cache)
watcher.start()

# Templates will reload automatically when files change
```

## Development

### Setup

```bash
git clone https://github.com/bogdan-pistol/promptlightning.git
cd promptlightning
uv sync
source .venv/bin/activate
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=promptlightning

# Run smoke tests
uv run python tests/smoke_test.py
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy promptlightning
```

### Development Commands

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

## Contributing

We welcome contributions! Join our community:

- 💬 **[Discord](https://discord.gg/QSRRcFjzE8)** - Join our Discord server for discussions and support
- 🐛 **Issues** - Report bugs or request features
- 🔀 **Pull Requests** - Submit improvements

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest`
5. Submit a pull request

## License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
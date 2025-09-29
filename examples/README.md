# Dakora Examples

This directory contains practical examples showing how to use Dakora in real applications.

## FastAPI + OpenAI Example

A complete FastAPI application demonstrating Dakora integration with OpenAI's latest Responses API and GPT-5.

### Features

- 🚀 **FastAPI endpoints** for template-based chat
- 🤖 **OpenAI Responses API** integration (recommended for new projects)
- 🧠 **GPT-5 with reasoning** capabilities and effort controls
- 📝 **Multiple template examples** (summarizer, analyzer, chat assistant)
- 🔍 **Template discovery** via REST API
- 📊 **Automatic logging** with Dakora's built-in system
- 🏥 **Health checks** and error handling

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Initialize Dakora:**
   ```bash
   # Copy example templates
   mkdir -p prompts
   cp templates/* prompts/

   # Or use the CLI to create a fresh project
   dakora init
   ```

4. **Run the API:**
   ```bash
   uvicorn fastapi_openai:app --reload
   ```

5. **Explore the API:**
   - Visit: http://localhost:8000/docs
   - Try the interactive Swagger UI

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/templates` | GET | List all available templates |
| `/templates/{id}` | GET | Get template details |
| `/chat` | POST | Generic chat with any template |
| `/summarize` | POST | Summarize text using summarizer template |
| `/analyze` | POST | Analyze content with analyzer template |
| `/health` | GET | Health check |

### Example Usage

**List templates:**
```bash
curl http://localhost:8000/templates
```

**Chat with assistant:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing in simple terms",
    "template_id": "chat_assistant",
    "model": "gpt-5",
    "reasoning_effort": "medium",
    "instructions": "Explain in a friendly, accessible way"
  }'
```

**Summarize text:**
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long article text here...",
    "max_bullets": 3
  }'
```

**Analyze content:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Business proposal text...",
    "analysis_type": "business"
  }'
```

### Template Examples

The example includes these template files:

- **`analyzer.yaml`** - Content analysis with different types (sentiment, technical, business)
- **`chat_assistant.yaml`** - General purpose chat assistant
- **`summarizer.yaml`** - Text summarization (created by `dakora init`)

### Configuration

The example uses `dakora.yaml` for configuration:

```yaml
registry: local
prompt_dir: ./prompts
logging:
  enabled: true
  backend: sqlite
  db_path: ./dakora.db
```

### Production Considerations

For production use, consider:

- **Authentication**: Add API key validation
- **Rate limiting**: Implement request throttling
- **Monitoring**: Add metrics and alerting
- **Error handling**: Improve error responses
- **Caching**: Cache template renders for repeated requests
- **Async**: Use async OpenAI calls for better performance

### Extending the Example

You can easily extend this example by:

1. **Adding new templates** in the `prompts/` directory
2. **Creating specialized endpoints** for specific use cases
3. **Adding middleware** for logging, authentication, etc.
4. **Integrating with other LLM providers** (Anthropic, etc.)
5. **Adding request validation** and better error handling
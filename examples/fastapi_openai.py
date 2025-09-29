#!/usr/bin/env python3
"""
FastAPI example showing how to use Dakora with OpenAI Responses API.

This example demonstrates:
- Loading prompt templates from YAML files
- Using templates in FastAPI endpoints
- Integration with OpenAI Responses API (recommended for new projects)
- GPT-5 model usage with reasoning capabilities
- Proper error handling and logging

Setup:
1. pip install fastapi uvicorn openai dakora
2. Set your OPENAI_API_KEY environment variable
3. Run: uvicorn fastapi_openai:app --reload
4. Visit: http://localhost:8000/docs
"""

import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from openai import OpenAI
from dakora import Vault

# Initialize FastAPI app
app = FastAPI(
    title="Dakora + OpenAI Responses API",
    description="Example API using Dakora with OpenAI's latest Responses API and GPT-5",
    version="1.0.0"
)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)

# Initialize Dakora (assumes you've run `dakora init`)
try:
    vault = Vault("dakora.yaml")
except Exception:
    # Fallback for demo purposes
    vault = Vault(prompt_dir="./prompts")

# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to process")
    template_id: str = Field(..., description="ID of the prompt template to use")
    model: str = Field(default="gpt-5", description="OpenAI model to use")
    reasoning_effort: str = Field(default="medium", description="Reasoning effort level: low, medium, high")
    instructions: Optional[str] = Field(default=None, description="Additional instructions for the model")

class ChatResponse(BaseModel):
    response: str
    template_used: str
    model: str
    reasoning_effort: str

class SummarizeRequest(BaseModel):
    text: str = Field(..., description="Text to summarize")
    max_bullets: Optional[int] = Field(default=3, description="Maximum number of bullet points")

class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Content to analyze")
    analysis_type: str = Field(default="general", description="Type of analysis to perform")

# Available templates endpoint
@app.get("/templates")
async def list_templates():
    """List all available prompt templates."""
    try:
        templates = vault.list()
        return {"templates": list(templates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get details about a specific template."""
    try:
        template = vault.get(template_id)
        return {
            "id": template.id,
            "version": template.version,
            "description": template.spec.description,
            "inputs": template.spec.inputs
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

# Generic chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_with_template(request: ChatRequest, background_tasks: BackgroundTasks):
    """Send a message using a specific prompt template."""
    try:
        # Get and render template
        template = vault.get(request.template_id)
        prompt = template.render(message=request.message)

        # Call OpenAI Responses API (recommended for new projects)
        response = client.responses.create(
            model=request.model,
            reasoning={"effort": request.reasoning_effort},
            instructions=request.instructions,
            input=prompt
        )

        # Extract response data using the convenient output_text property
        completion = response.output_text

        # Log execution in background (if logging is enabled)
        background_tasks.add_task(
            log_execution,
            template_id=request.template_id,
            inputs={"message": request.message},
            output=completion
        )

        return ChatResponse(
            response=completion,
            template_used=request.template_id,
            model=request.model,
            reasoning_effort=request.reasoning_effort
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Specific use case endpoints
@app.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    """Summarize text using the summarizer template."""
    try:
        template = vault.get("summarizer")

        # Use the template's run method for automatic logging
        result = template.run(
            lambda prompt: client.responses.create(
                model="gpt-5",
                reasoning={"effort": "low"},
                input=prompt
            ).output_text,
            input_text=request.text
        )

        return {"summary": result, "template_used": "summarizer"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_content(request: AnalyzeRequest):
    """Analyze content using the analyzer template."""
    try:
        # This assumes you have an 'analyzer' template
        template = vault.get("analyzer")

        result = template.run(
            lambda prompt: client.responses.create(
                model="gpt-5",
                reasoning={"effort": "medium"},  # Use medium effort for analysis
                input=prompt
            ).output_text,
            content=request.content,
            analysis_type=request.analysis_type
        )

        return {"analysis": result, "template_used": "analyzer"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test vault access
        templates = list(vault.list())
        return {
            "status": "healthy",
            "templates_loaded": len(templates),
            "openai_configured": bool(api_key)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Background task for logging
async def log_execution(template_id: str, inputs: Dict[str, Any], output: str):
    """Log template execution (runs in background)."""
    try:
        # This would be handled automatically if using template.run()
        # But for demonstration, you could add custom logging here
        print(f"Logged execution: {template_id} with inputs: {list(inputs.keys())}")
    except Exception as e:
        print(f"Logging failed: {e}")

# Error handler for template not found
@app.exception_handler(404)
async def template_not_found_handler(request, exc):
    return {"error": "Template not found", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
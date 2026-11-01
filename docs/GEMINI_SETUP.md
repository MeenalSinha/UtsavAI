# Google Gemini Integration & Setup Guide

## Architecture
PlanAI integrates with Google Gemini exclusively through the FastAPI backend (`apps/api/app/modules/ai/`). The frontend and browser never receive API keys or talk to Gemini directly.

Gemini integration is designed with a strict interface abstraction:
`apps/api/app/modules/ai/provider.py`:
- `StructuredGenerationProvider` (Protocol)
- `GeminiProvider` (Production implementation using official `google-genai` SDK)
- `FakeGenerationProvider` (Deterministic provider for CI/integration tests)

---

## Environment Configuration

Configure the following variables in `apps/api/.env`:

```env
# Gemini API Key (Secret — never commit)
GEMINI_API_KEY=your_gemini_api_key_here

# Default Gemini model (e.g. gemini-2.5-flash or gemini-2.5-pro)
GEMINI_MODEL=gemini-2.5-flash

# Generation safety and timeout controls
GEMINI_TIMEOUT_SECONDS=45
GEMINI_MAX_OUTPUT_TOKENS=4096
GEMINI_TEMPERATURE=0.3
GEMINI_RETRIES=2

# AI Feature flag and rate limiter
AI_FEATURE_ENABLED=true
AI_RATE_LIMIT_PER_MINUTE=20
```

---

## SDK Integration Details

The backend utilizes `google-genai` (v2.34+):
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)
response = client.models.generate_content(
    model=settings.gemini_model,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=PlanProposalPayload,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
    ),
)
```

---

## Error Handling & Fallbacks

1. **Missing or Invalid API Key:**
   When `GEMINI_API_KEY` is empty, unconfigured, or disabled via `AI_FEATURE_ENABLED=false`, the service raises `AIUnavailableError` (HTTP 503 Service Unavailable) with clear instructions for the administrator.
2. **Rate Limiting:**
   Exceeding `AI_RATE_LIMIT_PER_MINUTE` returns `AIRateLimitError` (HTTP 429 Too Many Requests).
3. **Structured Validation Failure:**
   If the model response fails Pydantic schema validation or domain constraints (such as cyclic task dependencies or missing client references), the backend catches this, rejects the unvalidated payload, logs an audit entry, and raises `AIValidationError` (HTTP 502 Bad Gateway) rather than corrupting the database.
4. **Deterministic Testing:**
   In automated unit and integration tests, `FakeGenerationProvider` is injected into `app.state.ai_provider`, providing deterministic, reproducible fixtures without making external network calls or incurring API costs.


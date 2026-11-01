"""AI provider abstractions and Gemini implementation."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import AIRateLimitError, AIUnavailableError, AIValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    raw_text: str
    parsed_json: dict[str, Any]
    model_id: str
    latency_ms: float


class StructuredGenerationProvider(Protocol):
    async def generate(
        self,
        *,
        task_name: str,
        system_instruction: str,
        user_input: str,
        response_schema: type[BaseModel] | dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> ProviderResponse: ...


class GeminiProvider:
    """Production provider using Google GenAI SDK."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._api_key = settings.gemini_api_key.get_secret_value()
        self._model = settings.gemini_model

    async def generate(
        self,
        *,
        task_name: str,
        system_instruction: str,
        user_input: str,
        response_schema: type[BaseModel] | dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> ProviderResponse:
        if not self._settings.ai_feature_enabled:
            raise AIUnavailableError("AI features are currently disabled.")
        if not self._api_key:
            raise AIUnavailableError("Gemini API key is not configured.")

        # Lazy import so domain/tests don't depend on Google SDK unconditionally
        try:
            from google import genai
            from google.genai import types
            from google.genai.errors import APIError
        except ImportError as exc:
            raise AIUnavailableError("Google GenAI SDK is not installed.") from exc

        client = genai.Client(api_key=self._api_key)
        start_time = time.perf_counter()

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self._settings.gemini_temperature,
            max_output_tokens=self._settings.gemini_max_output_tokens,
        )
        if response_schema is not None:
            config.response_mime_type = "application/json"
            if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
                config.response_schema = response_schema

        last_error: Exception | None = None
        retries = self._settings.gemini_retries

        for attempt in range(retries + 1):
            try:
                # The SDK supports async via client.aio
                res = await client.aio.models.generate_content(
                    model=self._model,
                    contents=user_input,
                    config=config,
                )
                raw_text = res.text or ""
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                parsed: dict[str, Any] = {}
                if response_schema is not None:
                    try:
                        clean_text = raw_text.strip()
                        if clean_text.startswith("```json"):
                            clean_text = clean_text.removeprefix("```json").removesuffix("```").strip()
                        elif clean_text.startswith("```"):
                            clean_text = clean_text.removeprefix("```").removesuffix("```").strip()
                        parsed = json.loads(clean_text)
                    except json.JSONDecodeError as err:
                        raise AIValidationError(f"Invalid JSON returned by AI model: {err}") from err

                return ProviderResponse(
                    raw_text=raw_text,
                    parsed_json=parsed,
                    model_id=self._model,
                    latency_ms=latency_ms,
                )
            except APIError as api_err:
                last_error = api_err
                code = getattr(api_err, "code", 500)
                if code == 429:
                    raise AIRateLimitError("Gemini quota or rate limit exceeded.") from api_err
                if attempt == retries:
                    raise AIUnavailableError(f"Gemini API error: {api_err.message}") from api_err
            except AIValidationError:
                raise
            except Exception as e:
                last_error = e
                if attempt == retries:
                    raise AIUnavailableError(f"AI generation failed: {e}") from e

            # Bounded backoff before retry
            import asyncio

            await asyncio.sleep(0.5 * (2**attempt))

        raise AIUnavailableError(f"AI generation failed after retries: {last_error}")


class FakeGenerationProvider:
    """Deterministic fake provider for testing and evaluation."""

    def __init__(self, canned_response: dict[str, Any] | None = None, canned_text: str = "") -> None:
        self.canned_response = canned_response or {}
        self.canned_text = canned_text or json.dumps(self.canned_response)
        self.call_count = 0
        self.last_prompt = ""
        self.last_system = ""

    async def generate(
        self,
        *,
        task_name: str,
        system_instruction: str,
        user_input: str,
        response_schema: type[BaseModel] | dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> ProviderResponse:
        self.call_count += 1
        self.last_prompt = user_input
        self.last_system = system_instruction
        return ProviderResponse(
            raw_text=self.canned_text,
            parsed_json=self.canned_response,
            model_id="fake-test-model",
            latency_ms=10.0,
        )

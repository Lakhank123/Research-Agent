import json
import logging
import re
import time
from typing import Optional, Type, TypeVar, Any
from pydantic import BaseModel, ValidationError
from groq import (
    Groq,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    APIConnectionError,
    InternalServerError,
    APIStatusError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMError(RuntimeError):
    """Base exception for LLM operations."""
    pass

class LLMAuthenticationError(LLMError):
    """Raised when the API key is missing, invalid, or unauthorized."""
    pass

class LLMModelNotFoundError(LLMError):
    """Raised when the requested model is not accessible or does not exist."""
    pass

class LLMRateLimitError(LLMError):
    """Raised when rate limits or quotas are exceeded."""
    pass

class LLMConnectionError(LLMError):
    """Raised on network timeouts or connectivity failures."""
    pass

class LLMServerError(LLMError):
    """Raised on upstream 5xx errors from Groq."""
    pass

class LLMSchemaError(LLMError):
    """Raised when output cannot be parsed into the expected JSON schema."""
    pass

def _clean_json_text(text: str) -> str:
    """Strip markdown code blocks, backticks, and extraneous whitespace."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()
    return raw

def _extract_outermost_json(text: str) -> str:
    cleaned = _clean_json_text(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end+1]
    return cleaned

def parse_json_safely(text: str) -> dict:
    cleaned = _clean_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_outermost_json(cleaned)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise LLMSchemaError(f"Failed to parse LLM response as JSON: {exc}") from exc

class GroqProvider:
    """Robust Groq provider adapter with preflight verification and categorized error handling."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b", fallback_model: Optional[str] = "openai/gpt-oss-20b"):
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise LLMAuthenticationError("GROQ_API_KEY is missing. Configure it in your .env file.")
        
        self.api_key = clean_key
        self.client = Groq(api_key=clean_key)
        self.requested_model = (model or "openai/gpt-oss-120b").strip()
        self.fallback_model = (fallback_model or "openai/gpt-oss-20b").strip() if fallback_model else None
        
        # Verified active model
        self.active_model = self.requested_model
        self.model_status_note = ""
        self._available_models: list[str] = []
        self._preflight_completed = False

    def preflight_model(self) -> str:
        """Verify model accessibility against the Groq API models list."""
        if self._preflight_completed:
            return self.active_model

        try:
            models_response = self.client.models.list()
            active_ids = [m.id for m in models_response.data if getattr(m, "active", True)]
            self._available_models = active_ids

            if self.requested_model in active_ids:
                self.active_model = self.requested_model
                self.model_status_note = f"Active model '{self.active_model}' verified."
                self._preflight_completed = True
                return self.active_model

            # Requested model not available; inspect fallbacks
            candidates = ["openai/gpt-oss-120b"]
            if self.fallback_model and self.fallback_model != "openai/gpt-oss-120b":
                candidates.append(self.fallback_model)
            candidates.extend(["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile"])
            
            selected_fallback = None
            for candidate in candidates:
                if candidate in active_ids:
                    selected_fallback = candidate
                    break

            if selected_fallback:
                self.active_model = selected_fallback
                self.model_status_note = (
                    f"Configured model '{self.requested_model}' is not accessible with your key. "
                    f"Switched to verified fallback model '{self.active_model}'."
                )
                self._preflight_completed = True
                return self.active_model

            # No recognized candidate is available
            sample_available = ", ".join(active_ids[:6])
            raise LLMModelNotFoundError(
                f"Configured model '{self.requested_model}' not found in accessible models. "
                f"Available models for this key: {sample_available}"
            )

        except AuthenticationError as exc:
            raise LLMAuthenticationError(f"Invalid Groq API key: {exc.message if hasattr(exc, 'message') else exc}") from exc
        except PermissionDeniedError as exc:
            raise LLMAuthenticationError(f"Groq API key permissions error: {exc}") from exc
        except (LLMModelNotFoundError, LLMAuthenticationError):
            raise
        except Exception as exc:
            # If models endpoint check fails due to temporary network, keep configured model and let execution test it
            self.active_model = self.requested_model
            self.model_status_note = f"Preflight check warning: could not verify models list ({type(exc).__name__}). Using '{self.active_model}'."
            self._preflight_completed = True
            return self.active_model

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> Any:
        """Generate structured JSON using Groq with bounded retries on transient errors."""
        self.preflight_model()
        model_to_use = self.active_model

        # Groq json_object mode requires the string 'json' in system or user prompt
        sys_prompt = system_prompt
        if "json" not in sys_prompt.lower() and "json" not in user_prompt.lower():
            sys_prompt += "\nOutput your entire response strictly as a valid JSON object."

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                data = parse_json_safely(content)

                if schema is not None:
                    try:
                        return schema.model_validate(data)
                    except ValidationError as val_err:
                        raise LLMSchemaError(f"Output schema validation failed: {val_err}") from val_err
                
                return data

            except AuthenticationError as exc:
                # Fatal: do not retry authentication errors
                raise LLMAuthenticationError(f"Groq authentication failed: {exc}") from exc
            except (NotFoundError, PermissionDeniedError) as exc:
                # Fatal: model not found or forbidden
                raise LLMModelNotFoundError(f"Groq model access error for '{model_to_use}': {exc}") from exc
            except RateLimitError as exc:
                last_error = LLMRateLimitError(f"Groq rate limit encountered: {exc}")
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
                raise last_error from exc
            except APIConnectionError as exc:
                last_error = LLMConnectionError(f"Groq connection failure: {exc}")
                if attempt < max_retries:
                    time.sleep(1.5)
                    continue
                raise last_error from exc
            except InternalServerError as exc:
                last_error = LLMServerError(f"Groq server error (5xx): {exc}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                raise last_error from exc
            except LLMSchemaError as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                raise
            except Exception as exc:
                last_error = LLMError(f"Groq unexpected error: {exc}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                raise last_error from exc

        raise LLMError(f"LLM request failed after {max_retries} retries: {last_error}")

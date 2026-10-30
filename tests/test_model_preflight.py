import pytest
from core.llm import (
    GroqProvider,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    _clean_json_text,
    _extract_outermost_json,
    parse_json_safely
)

def test_missing_api_key_raises_auth_error():
    with pytest.raises(LLMAuthenticationError):
        GroqProvider(api_key="")

def test_clean_json_fences():
    fenced = "```json\n{\"status\": \"ok\", \"count\": 42}\n```"
    assert parse_json_safely(fenced) == {"status": "ok", "count": 42}

def test_extract_outermost_json_with_commentary():
    text = "Here is your requested research data:\n{\"result\": true}\nLet me know if you need anything else."
    assert parse_json_safely(text) == {"result": True}

def test_invalid_json_raises_schema_error():
    from core.llm import LLMSchemaError
    with pytest.raises(LLMSchemaError):
        parse_json_safely("Not valid JSON at all")


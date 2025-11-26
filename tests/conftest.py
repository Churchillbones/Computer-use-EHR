"""
Pytest configuration and fixtures for Computer Use Demo tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("VA_OPENAI_BASE_URL", "https://test-api.example.com/openai/v1/chat/completions/")
    monkeypatch.setenv("VA_OPENAI_RESPONSES_URL", "https://test-api.example.com/openai/v1/responses/")
    monkeypatch.setenv("VA_OPENAI_API_KEY", "test-api-key-1")
    monkeypatch.setenv("VA_OPENAI_API_KEY_2", "test-api-key-2")
    monkeypatch.setenv("VA_OPENAI_API_VERSION", "2025-01-01-preview")
    monkeypatch.setenv("VA_GPT5_DEPLOYMENT", "gpt-5")
    monkeypatch.setenv("VA_GPT5_MODEL_NAME", "gpt-5")
    monkeypatch.setenv("VA_COMPUTER_USE_DEPLOYMENT", "computer-use-preview")
    monkeypatch.setenv("DISPLAY_WIDTH", "1920")
    monkeypatch.setenv("DISPLAY_HEIGHT", "1080")
    monkeypatch.setenv("MAX_ITERATIONS", "10")


@pytest.fixture
def sample_api_key():
    """Provide a sample API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def sample_base_url():
    """Provide a sample base URL for testing."""
    return "https://test-api.example.com/openai/v1/chat/completions"


@pytest.fixture
def sample_responses_url():
    """Provide a sample responses URL for testing."""
    return "https://test-api.example.com/openai/v1/responses"


@pytest.fixture
def sample_screenshot_base64():
    """Provide a sample base64 screenshot for testing (1x1 white PNG)."""
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.fixture
def mock_chat_response():
    """Provide a mock chat completions response."""
    return {
        "id": "chatcmpl-12345",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "gpt-5",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! This is a test response."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    }


@pytest.fixture
def mock_responses_api_response():
    """Provide a mock responses API response with computer call."""
    return {
        "id": "resp-12345",
        "object": "response",
        "created": 1700000000,
        "model": "computer-use-preview",
        "output": [
            {
                "type": "reasoning",
                "id": "rs-12345",
                "summary": [{
                    "type": "summary_text",
                    "text": "Taking a screenshot to assess the current state."
                }]
            },
            {
                "type": "computer_call",
                "id": "cu-12345",
                "call_id": "call-12345",
                "action": {
                    "type": "screenshot"
                },
                "pending_safety_checks": [],
                "status": "completed"
            }
        ]
    }


@pytest.fixture
def mock_responses_api_click_response():
    """Provide a mock responses API response with click action."""
    return {
        "id": "resp-67890",
        "object": "response",
        "created": 1700000000,
        "model": "computer-use-preview",
        "output": [
            {
                "type": "computer_call",
                "id": "cu-67890",
                "call_id": "call-67890",
                "action": {
                    "type": "click",
                    "button": "left",
                    "x": 500,
                    "y": 300
                },
                "pending_safety_checks": [],
                "status": "completed"
            }
        ]
    }


@pytest.fixture
def mock_responses_api_type_response():
    """Provide a mock responses API response with type action."""
    return {
        "id": "resp-11111",
        "object": "response",
        "created": 1700000000,
        "model": "computer-use-preview",
        "output": [
            {
                "type": "computer_call",
                "id": "cu-11111",
                "call_id": "call-11111",
                "action": {
                    "type": "type",
                    "text": "Patient presents with symptoms of..."
                },
                "pending_safety_checks": [],
                "status": "completed"
            }
        ]
    }


@pytest.fixture
def mock_responses_api_safety_check_response():
    """Provide a mock responses API response with safety check."""
    return {
        "id": "resp-safety",
        "object": "response",
        "created": 1700000000,
        "model": "computer-use-preview",
        "output": [
            {
                "type": "computer_call",
                "id": "cu-safety",
                "call_id": "call-safety",
                "action": {
                    "type": "click",
                    "button": "left",
                    "x": 100,
                    "y": 200
                },
                "pending_safety_checks": [
                    {
                        "id": "sc-12345",
                        "code": "sensitive_domain",
                        "message": "This action involves a sensitive domain. Please confirm."
                    }
                ],
                "status": "completed"
            }
        ]
    }


@pytest.fixture
def mock_requests_post():
    """Provide a mock for requests.post."""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_pyautogui():
    """Provide a mock for pyautogui module."""
    with patch.dict('sys.modules', {'pyautogui': MagicMock()}):
        import pyautogui
        yield pyautogui

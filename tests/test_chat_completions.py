"""
Tests for ChatCompletionsClient.

Following TDD principles - these tests define expected behavior
for the Chat Completions API client.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from src.clients.chat_client import ChatCompletionsClient


class TestChatCompletionsClientInit:
    """Tests for ChatCompletionsClient initialization."""
    
    def test_init_with_valid_params_creates_client(
        self, sample_base_url, sample_api_key
    ):
        """Test that client initializes with valid parameters."""
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key,
            model="gpt-5"
        )
        
        assert client.base_url == sample_base_url
        assert client.model == "gpt-5"
        assert client.api_version == "2025-01-01-preview"
    
    def test_init_with_empty_base_url_raises_value_error(self, sample_api_key):
        """Test that empty base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            ChatCompletionsClient(base_url="", api_key=sample_api_key)
    
    def test_init_with_empty_api_key_raises_value_error(self, sample_base_url):
        """Test that empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            ChatCompletionsClient(base_url=sample_base_url, api_key="")
    
    def test_init_strips_trailing_slash_from_url(self, sample_api_key):
        """Test that trailing slash is removed from base_url."""
        client = ChatCompletionsClient(
            base_url="https://api.example.com/v1/",
            api_key=sample_api_key
        )
        
        assert client.base_url == "https://api.example.com/v1"
    
    def test_init_with_custom_api_version(self, sample_base_url, sample_api_key):
        """Test that custom API version is accepted."""
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key,
            api_version="2024-12-01"
        )
        
        assert client.api_version == "2024-12-01"


class TestChatCompletionsClientSendMessage:
    """Tests for ChatCompletionsClient.send_message method."""
    
    def test_send_message_makes_post_request(
        self, sample_base_url, sample_api_key, mock_requests_post, mock_chat_response
    ):
        """Test that send_message makes a POST request to the API."""
        mock_requests_post.return_value.json.return_value = mock_chat_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        result = client.send_message("Hello, world!")
        
        mock_requests_post.assert_called_once()
        assert result == mock_chat_response
    
    def test_send_message_includes_correct_headers(
        self, sample_base_url, sample_api_key, mock_requests_post, mock_chat_response
    ):
        """Test that send_message includes correct API headers."""
        mock_requests_post.return_value.json.return_value = mock_chat_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        client.send_message("Test message")
        
        call_kwargs = mock_requests_post.call_args.kwargs
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["api-key"] == sample_api_key
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
    
    def test_send_message_with_system_prompt(
        self, sample_base_url, sample_api_key, mock_requests_post, mock_chat_response
    ):
        """Test that system prompt is included in messages."""
        mock_requests_post.return_value.json.return_value = mock_chat_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        client.send_message(
            message="Hello",
            system_prompt="You are a helpful assistant."
        )
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are a helpful assistant."
    
    def test_send_message_raises_on_request_failure(
        self, sample_base_url, sample_api_key, mock_requests_post
    ):
        """Test that RequestException is raised on API failure."""
        mock_requests_post.side_effect = requests.RequestException("Connection failed")
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        with pytest.raises(requests.RequestException):
            client.send_message("Test message")


class TestChatCompletionsClientGetCompletionText:
    """Tests for ChatCompletionsClient.get_completion_text method."""
    
    def test_get_completion_text_extracts_content(
        self, sample_base_url, sample_api_key, mock_chat_response
    ):
        """Test that completion text is extracted from response."""
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        text = client.get_completion_text(mock_chat_response)
        
        assert text == "Hello! This is a test response."
    
    def test_get_completion_text_returns_none_for_invalid_response(
        self, sample_base_url, sample_api_key
    ):
        """Test that None is returned for invalid response structure."""
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        invalid_response = {"choices": []}
        text = client.get_completion_text(invalid_response)
        
        assert text is None


class TestChatCompletionsClientTestConnection:
    """Tests for ChatCompletionsClient.test_connection method."""
    
    def test_test_connection_returns_true_on_success(
        self, sample_base_url, sample_api_key, mock_requests_post, mock_chat_response
    ):
        """Test that test_connection returns True on successful connection."""
        mock_requests_post.return_value.json.return_value = mock_chat_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        result = client.test_connection()
        
        assert result is True
    
    def test_test_connection_returns_false_on_failure(
        self, sample_base_url, sample_api_key, mock_requests_post
    ):
        """Test that test_connection returns False on connection failure."""
        mock_requests_post.side_effect = requests.RequestException("Connection failed")
        
        client = ChatCompletionsClient(
            base_url=sample_base_url,
            api_key=sample_api_key
        )
        
        result = client.test_connection()
        
        assert result is False

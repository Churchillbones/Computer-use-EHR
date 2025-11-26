"""
Tests for ResponsesAPIClient.

Following TDD principles - these tests define expected behavior
for the Responses API client used with Computer Use.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from src.clients.responses_client import ResponsesAPIClient


class TestResponsesAPIClientInit:
    """Tests for ResponsesAPIClient initialization."""
    
    def test_init_with_valid_params_creates_client(
        self, sample_responses_url, sample_api_key
    ):
        """Test that client initializes with valid parameters."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key,
            model="computer-use-preview"
        )
        
        assert client.base_url == sample_responses_url
        assert client.model == "computer-use-preview"
        assert client.display_width == 1920
        assert client.display_height == 1080
    
    def test_init_with_custom_display_dimensions(
        self, sample_responses_url, sample_api_key
    ):
        """Test that custom display dimensions are accepted."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key,
            display_width=2560,
            display_height=1440
        )
        
        assert client.display_width == 2560
        assert client.display_height == 1440
    
    def test_init_with_empty_base_url_raises_value_error(self, sample_api_key):
        """Test that empty base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            ResponsesAPIClient(base_url="", api_key=sample_api_key)
    
    def test_init_with_empty_api_key_raises_value_error(self, sample_responses_url):
        """Test that empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            ResponsesAPIClient(base_url=sample_responses_url, api_key="")


class TestResponsesAPIClientCreateResponse:
    """Tests for ResponsesAPIClient.create_response method."""
    
    def test_create_response_makes_post_request(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response
    ):
        """Test that create_response makes a POST request to the API."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        result = client.create_response("Take a screenshot")
        
        mock_requests_post.assert_called_once()
        assert result == mock_responses_api_response
    
    def test_create_response_includes_computer_tool_by_default(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response
    ):
        """Test that computer use tool is included by default."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        client.create_response("Take a screenshot")
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert "tools" in payload
        assert payload["tools"][0]["type"] == "computer_use_preview"
    
    def test_create_response_with_screenshot(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response, sample_screenshot_base64
    ):
        """Test that screenshot is included in request when provided."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        client.create_response(
            task="Click the button",
            screenshot_base64=sample_screenshot_base64
        )
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        # Check that input contains image
        input_content = payload["input"][0]["content"]
        image_inputs = [i for i in input_content if i["type"] == "input_image"]
        
        assert len(image_inputs) == 1
        assert sample_screenshot_base64 in image_inputs[0]["image_url"]
    
    def test_create_response_with_previous_response_id(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response
    ):
        """Test that previous_response_id is included when provided."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        client.create_response(
            task="Continue the task",
            previous_response_id="resp-12345"
        )
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert payload["previous_response_id"] == "resp-12345"
    
    def test_create_response_without_computer_tool(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response
    ):
        """Test that computer tool can be excluded."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        client.create_response(
            task="Just respond with text",
            include_computer_tool=False
        )
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert "tools" not in payload
    
    def test_create_response_raises_on_request_failure(
        self, sample_responses_url, sample_api_key, mock_requests_post
    ):
        """Test that RequestException is raised on API failure."""
        mock_requests_post.side_effect = requests.RequestException("Connection failed")
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        with pytest.raises(requests.RequestException):
            client.create_response("Test task")


class TestResponsesAPIClientExtractComputerCalls:
    """Tests for ResponsesAPIClient.extract_computer_calls method."""
    
    def test_extract_computer_calls_returns_calls(
        self, sample_responses_url, sample_api_key, mock_responses_api_response
    ):
        """Test that computer calls are extracted from response."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        calls = client.extract_computer_calls(mock_responses_api_response)
        
        assert len(calls) == 1
        assert calls[0]["type"] == "computer_call"
        assert calls[0]["action"]["type"] == "screenshot"
    
    def test_extract_computer_calls_returns_empty_for_no_calls(
        self, sample_responses_url, sample_api_key
    ):
        """Test that empty list is returned when no computer calls exist."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        response = {"output": [{"type": "text", "text": "Hello"}]}
        calls = client.extract_computer_calls(response)
        
        assert calls == []
    
    def test_extract_computer_calls_handles_click_action(
        self, sample_responses_url, sample_api_key, mock_responses_api_click_response
    ):
        """Test that click actions are properly extracted."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        calls = client.extract_computer_calls(mock_responses_api_click_response)
        
        assert len(calls) == 1
        assert calls[0]["action"]["type"] == "click"
        assert calls[0]["action"]["x"] == 500
        assert calls[0]["action"]["y"] == 300


class TestResponsesAPIClientExtractTextOutput:
    """Tests for ResponsesAPIClient.extract_text_output method."""
    
    def test_extract_text_output_returns_text(
        self, sample_responses_url, sample_api_key
    ):
        """Test that text output is extracted from response."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        response = {
            "output": [
                {"type": "text", "text": "Task completed successfully."}
            ]
        }
        
        text = client.extract_text_output(response)
        
        assert text == "Task completed successfully."
    
    def test_extract_text_output_returns_none_for_no_text(
        self, sample_responses_url, sample_api_key, mock_responses_api_response
    ):
        """Test that None is returned when no text output exists."""
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        text = client.extract_text_output(mock_responses_api_response)
        
        assert text is None


class TestResponsesAPIClientSendScreenshot:
    """Tests for ResponsesAPIClient.send_screenshot method."""
    
    def test_send_screenshot_makes_post_request(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response, sample_screenshot_base64
    ):
        """Test that send_screenshot makes a POST request."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        result = client.send_screenshot(
            previous_response_id="resp-12345",
            call_id="call-12345",
            screenshot_base64=sample_screenshot_base64
        )
        
        mock_requests_post.assert_called_once()
        assert result == mock_responses_api_response
    
    def test_send_screenshot_includes_call_id(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response, sample_screenshot_base64
    ):
        """Test that call_id is included in request."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        client.send_screenshot(
            previous_response_id="resp-12345",
            call_id="call-67890",
            screenshot_base64=sample_screenshot_base64
        )
        
        call_kwargs = mock_requests_post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert payload["input"][0]["call_id"] == "call-67890"


class TestResponsesAPIClientTestConnection:
    """Tests for ResponsesAPIClient.test_connection method."""
    
    def test_test_connection_returns_true_on_success(
        self, sample_responses_url, sample_api_key, mock_requests_post,
        mock_responses_api_response
    ):
        """Test that test_connection returns True on successful connection."""
        mock_requests_post.return_value.json.return_value = mock_responses_api_response
        mock_requests_post.return_value.raise_for_status = Mock()
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        result = client.test_connection()
        
        assert result is True
    
    def test_test_connection_returns_false_on_failure(
        self, sample_responses_url, sample_api_key, mock_requests_post
    ):
        """Test that test_connection returns False on connection failure."""
        mock_requests_post.side_effect = requests.RequestException("Connection failed")
        
        client = ResponsesAPIClient(
            base_url=sample_responses_url,
            api_key=sample_api_key
        )
        
        result = client.test_connection()
        
        assert result is False

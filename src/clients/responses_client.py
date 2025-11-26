"""
Responses API client for Azure OpenAI.

Provides functionality to interact with the /v1/responses endpoint,
which is used for the Computer Use preview feature.
"""

from typing import Any, Optional
import logging
import requests

from src.clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class ResponsesAPIClient(BaseClient):
    """
    Client for Azure OpenAI Responses API.
    
    Handles communication with the /v1/responses endpoint,
    which is required for Computer Use functionality.
    
    Attributes:
        model: The model/deployment name to use.
        display_width: Screen width for computer use.
        display_height: Screen height for computer use.
    
    Example:
        >>> client = ResponsesAPIClient(
        ...     base_url="https://api.example.com/openai/v1/responses",
        ...     api_key="your-api-key",
        ...     model="computer-use-preview"
        ... )
        >>> response = client.create_response("Take a screenshot")
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "computer-use-preview",
        api_version: str = "2025-01-01-preview",
        display_width: int = 1920,
        display_height: int = 1080
    ) -> None:
        """
        Initialize the Responses API client.
        
        Args:
            base_url: The base URL for responses endpoint.
            api_key: The API key for authentication.
            model: The model/deployment name to use.
            api_version: The API version string.
            display_width: Screen width in pixels.
            display_height: Screen height in pixels.
        """
        super().__init__(base_url, api_key, api_version)
        self._model = model
        self._display_width = display_width
        self._display_height = display_height
        logger.info(f"ResponsesAPIClient initialized with model: {model}")
    
    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model
    
    @property
    def display_width(self) -> int:
        """Get the display width."""
        return self._display_width
    
    @property
    def display_height(self) -> int:
        """Get the display height."""
        return self._display_height
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Responses API.
        
        Sends a simple test request to verify connectivity.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            response = self.create_response(
                task="This is a connection test. Please respond with 'OK'.",
                include_computer_tool=False
            )
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def create_response(
        self,
        task: str,
        screenshot_base64: Optional[str] = None,
        include_computer_tool: bool = True,
        environment: str = "windows",
        previous_response_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """
        Create a response using the Responses API.
        
        Args:
            task: The task description for the model.
            screenshot_base64: Base64-encoded screenshot image.
            include_computer_tool: Whether to include computer use tool.
            environment: The environment type (windows, mac, linux, browser).
            previous_response_id: ID of previous response for chaining.
        
        Returns:
            The API response as a dictionary, or None if request fails.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        # Build input content
        input_content = [{
            "type": "input_text",
            "text": task
        }]
        
        if screenshot_base64:
            input_content.append({
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}"
            })
        
        payload: dict[str, Any] = {
            "model": self._model,
            "input": [{
                "role": "user",
                "content": input_content
            }],
            "truncation": "auto"
        }
        
        # Add computer use tool if requested
        if include_computer_tool:
            payload["tools"] = [{
                "type": "computer_use_preview",
                "display_width": self._display_width,
                "display_height": self._display_height,
                "environment": environment
            }]
        
        # Add previous response ID for chaining
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        logger.info(f"Creating response at {self._base_url}")
        logger.debug(f"Payload keys: {payload.keys()}")
        
        try:
            response = requests.post(
                self._base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Response created successfully")
            logger.debug(f"Response ID: {result.get('id', 'N/A')}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def send_screenshot(
        self,
        previous_response_id: str,
        call_id: str,
        screenshot_base64: str,
        current_url: Optional[str] = None,
        acknowledged_safety_checks: Optional[list[dict]] = None
    ) -> Optional[dict[str, Any]]:
        """
        Send a screenshot as output from a computer call.
        
        This is used in the computer use loop to provide
        the model with updated state after an action.
        
        Args:
            previous_response_id: ID of the previous response.
            call_id: ID of the computer call being responded to.
            screenshot_base64: Base64-encoded screenshot image.
            current_url: Optional current URL for context.
            acknowledged_safety_checks: Safety checks to acknowledge.
        
        Returns:
            The API response as a dictionary, or None if request fails.
        """
        input_content: dict[str, Any] = {
            "type": "computer_call_output",
            "call_id": call_id,
            "output": {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}"
            }
        }
        
        if current_url:
            input_content["current_url"] = current_url
        
        if acknowledged_safety_checks:
            input_content["acknowledged_safety_checks"] = acknowledged_safety_checks
        
        payload = {
            "model": self._model,
            "previous_response_id": previous_response_id,
            "tools": [{
                "type": "computer_use_preview",
                "display_width": self._display_width,
                "display_height": self._display_height,
                "environment": "windows"
            }],
            "input": [input_content],
            "truncation": "auto"
        }
        
        logger.info(f"Sending screenshot for call_id: {call_id}")
        
        try:
            response = requests.post(
                self._base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Screenshot sent successfully")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def extract_computer_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract computer calls from an API response.
        
        Args:
            response: The API response dictionary.
        
        Returns:
            List of computer call dictionaries.
        """
        output = response.get("output", [])
        computer_calls = [
            item for item in output
            if isinstance(item, dict) and item.get("type") == "computer_call"
        ]
        logger.debug(f"Extracted {len(computer_calls)} computer calls")
        return computer_calls
    
    def extract_text_output(self, response: dict[str, Any]) -> Optional[str]:
        """
        Extract text output from an API response.
        
        Args:
            response: The API response dictionary.
        
        Returns:
            The text content, or None if not found.
        """
        output = response.get("output", [])
        for item in output:
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text")
        return None

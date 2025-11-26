"""
Chat Completions client for Azure OpenAI API.

Provides functionality to interact with the /v1/chat/completions endpoint.
"""

from typing import Any, Optional
import logging
import requests

from src.clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class ChatCompletionsClient(BaseClient):
    """
    Client for Azure OpenAI Chat Completions API.
    
    Handles communication with the /v1/chat/completions endpoint
    for standard chat-based interactions with GPT models.
    
    Attributes:
        model: The model/deployment name to use.
    
    Example:
        >>> client = ChatCompletionsClient(
        ...     base_url="https://api.example.com/openai/v1/chat/completions",
        ...     api_key="your-api-key",
        ...     model="gpt-5"
        ... )
        >>> response = client.send_message("Hello, world!")
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-5",
        api_version: str = "2025-01-01-preview"
    ) -> None:
        """
        Initialize the Chat Completions client.
        
        Args:
            base_url: The base URL for chat completions endpoint.
            api_key: The API key for authentication.
            model: The model/deployment name to use.
            api_version: The API version string.
        """
        super().__init__(base_url, api_key, api_version)
        self._model = model
        logger.info(f"ChatCompletionsClient initialized with model: {model}")
    
    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Chat Completions API.
        
        Sends a simple test message to verify connectivity.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            response = self.send_message(
                message="Hello, this is a connection test.",
                max_tokens=10
            )
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def send_message(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[dict[str, Any]]:
        """
        Send a message to the Chat Completions API.
        
        Args:
            message: The user message to send.
            system_prompt: Optional system prompt to set context.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-2).
        
        Returns:
            The API response as a dictionary, or None if request fails.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": message
        })
        
        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        logger.info(f"Sending message to {self._base_url}")
        logger.debug(f"Payload: {payload}")
        
        try:
            response = requests.post(
                self._base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Message sent successfully")
            logger.debug(f"Response: {result}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_completion_text(self, response: dict[str, Any]) -> Optional[str]:
        """
        Extract the completion text from an API response.
        
        Args:
            response: The API response dictionary.
        
        Returns:
            The completion text, or None if not found.
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract completion text: {e}")
            return None

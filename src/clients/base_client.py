"""
Base client for Azure OpenAI API communication.

Provides abstract base class with common functionality for all API clients.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """
    Abstract base class for Azure OpenAI API clients.
    
    Provides common functionality for authentication and error handling.
    Subclasses must implement the `test_connection` method.
    
    Attributes:
        base_url: The base URL for API requests.
        api_key: The API key for authentication.
        api_version: The API version string.
    
    Example:
        >>> class MyClient(BaseClient):
        ...     def test_connection(self) -> bool:
        ...         return True
        >>> client = MyClient(base_url="https://api.example.com", api_key="key")
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_version: str = "2025-01-01-preview"
    ) -> None:
        """
        Initialize the base client.
        
        Args:
            base_url: The base URL for API requests.
            api_key: The API key for authentication.
            api_version: The API version string.
        
        Raises:
            ValueError: If base_url or api_key is empty.
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")
        if not api_key:
            raise ValueError("api_key cannot be empty")
        
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._api_version = api_version
        
        logger.info(f"Initialized {self.__class__.__name__} with base_url: {self._base_url}")
    
    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._base_url
    
    @property
    def api_version(self) -> str:
        """Get the API version."""
        return self._api_version
    
    def _get_headers(self) -> dict[str, str]:
        """
        Get common headers for API requests.
        
        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Content-Type": "application/json",
            "api-key": self._api_key,
        }
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the API.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        pass

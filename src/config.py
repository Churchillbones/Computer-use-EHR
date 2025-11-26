"""
Configuration management for the Computer Use Demo.

Loads environment variables from .env file and provides
typed configuration values.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration from environment variables.
    
    All configuration values are loaded from environment variables,
    with sensible defaults where appropriate.
    
    Attributes:
        OPENAI_BASE_URL: Base URL for chat completions endpoint.
        OPENAI_RESPONSES_URL: Base URL for responses API endpoint.
        OPENAI_API_KEY: Primary API key for authentication.
        OPENAI_API_KEY_2: Secondary API key for testing.
        OPENAI_API_VERSION: API version string.
        GPT5_DEPLOYMENT: Deployment name for GPT-5 model.
        GPT5_MODEL_NAME: Model name for GPT-5.
        COMPUTER_USE_DEPLOYMENT: Deployment name for computer-use-preview.
        DISPLAY_WIDTH: Screen width in pixels.
        DISPLAY_HEIGHT: Screen height in pixels.
        MAX_ITERATIONS: Maximum iterations for automation loop.
    
    Example:
        >>> from src.config import Config
        >>> config = Config()
        >>> print(config.GPT5_DEPLOYMENT)
        'gpt-5'
    """
    
    # API Endpoints
    OPENAI_BASE_URL: str = os.getenv("VA_OPENAI_BASE_URL", "")
    OPENAI_RESPONSES_URL: str = os.getenv("VA_OPENAI_RESPONSES_URL", "")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("VA_OPENAI_API_KEY", "")
    OPENAI_API_KEY_2: str = os.getenv("VA_OPENAI_API_KEY_2", "")
    
    # API Version
    OPENAI_API_VERSION: str = os.getenv("VA_OPENAI_API_VERSION", "2025-01-01-preview")
    
    # Model Configuration
    GPT5_DEPLOYMENT: str = os.getenv("VA_GPT5_DEPLOYMENT", "gpt-5")
    GPT5_MODEL_NAME: str = os.getenv("VA_GPT5_MODEL_NAME", "gpt-5")
    COMPUTER_USE_DEPLOYMENT: str = os.getenv("VA_COMPUTER_USE_DEPLOYMENT", "computer-use-preview")
    
    # Display Settings
    DISPLAY_WIDTH: int = int(os.getenv("DISPLAY_WIDTH", "1920"))
    DISPLAY_HEIGHT: int = int(os.getenv("DISPLAY_HEIGHT", "1080"))
    
    # Automation Settings
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that required configuration values are set.
        
        Returns:
            List of missing or invalid configuration keys.
        """
        errors = []
        
        if not cls.OPENAI_BASE_URL:
            errors.append("VA_OPENAI_BASE_URL is not set")
        if not cls.OPENAI_API_KEY:
            errors.append("VA_OPENAI_API_KEY is not set")
        if not cls.GPT5_DEPLOYMENT:
            errors.append("VA_GPT5_DEPLOYMENT is not set")
            
        return errors
    
    @classmethod
    def is_valid(cls) -> bool:
        """
        Check if configuration is valid.
        
        Returns:
            True if all required configuration is set, False otherwise.
        """
        return len(cls.validate()) == 0


# Create a singleton instance for easy access
config = Config()

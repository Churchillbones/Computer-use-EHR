"""
Screen controller for capturing screenshots.

Provides functionality to capture the screen and convert to base64
for use with the Computer Use API.
"""

import base64
import io
import logging
from typing import Tuple, Optional

import pyautogui
from PIL import Image

logger = logging.getLogger(__name__)


class ScreenController:
    """
    Controller for screen capture operations.
    
    Handles capturing screenshots and converting them to base64 format
    for transmission to the Azure OpenAI Computer Use API.
    
    Attributes:
        display_width: Screen width in pixels.
        display_height: Screen height in pixels.
    
    Example:
        >>> controller = ScreenController()
        >>> screenshot = controller.capture_screenshot()
        >>> base64_str = controller.screenshot_to_base64()
    """
    
    def __init__(
        self,
        display_width: Optional[int] = None,
        display_height: Optional[int] = None
    ) -> None:
        """
        Initialize the screen controller.
        
        Args:
            display_width: Override screen width. If None, uses actual screen size.
            display_height: Override screen height. If None, uses actual screen size.
        """
        actual_width, actual_height = pyautogui.size()
        
        self._display_width = display_width or actual_width
        self._display_height = display_height or actual_height
        self._last_screenshot: Optional[Image.Image] = None
        
        logger.info(
            f"ScreenController initialized with dimensions: "
            f"{self._display_width}x{self._display_height}"
        )
    
    @property
    def display_width(self) -> int:
        """Get the display width."""
        return self._display_width
    
    @property
    def display_height(self) -> int:
        """Get the display height."""
        return self._display_height
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the current screen size.
        
        Returns:
            Tuple of (width, height) in pixels.
        """
        return pyautogui.size()
    
    def capture_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Capture a screenshot of the screen.
        
        Args:
            region: Optional tuple of (x, y, width, height) for partial screenshot.
        
        Returns:
            PIL Image object of the screenshot.
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            self._last_screenshot = screenshot
            logger.debug(f"Screenshot captured: {screenshot.size}")
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise
    
    def screenshot_to_base64(
        self,
        screenshot: Optional[Image.Image] = None,
        format: str = "PNG"
    ) -> str:
        """
        Convert a screenshot to base64-encoded string.
        
        Args:
            screenshot: PIL Image to convert. If None, captures new screenshot.
            format: Image format (PNG, JPEG, etc.).
        
        Returns:
            Base64-encoded string of the image.
        """
        if screenshot is None:
            screenshot = self.capture_screenshot()
        
        buffer = io.BytesIO()
        screenshot.save(buffer, format=format)
        buffer.seek(0)
        
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        logger.debug(f"Screenshot converted to base64: {len(base64_str)} chars")
        
        return base64_str
    
    def get_last_screenshot(self) -> Optional[Image.Image]:
        """
        Get the last captured screenshot.
        
        Returns:
            The last captured screenshot, or None if no screenshot taken.
        """
        return self._last_screenshot
    
    def save_screenshot(
        self,
        filepath: str,
        screenshot: Optional[Image.Image] = None
    ) -> None:
        """
        Save a screenshot to a file.
        
        Args:
            filepath: Path to save the screenshot.
            screenshot: PIL Image to save. If None, uses last screenshot.
        
        Raises:
            ValueError: If no screenshot is available.
        """
        if screenshot is None:
            screenshot = self._last_screenshot
        
        if screenshot is None:
            raise ValueError("No screenshot available to save")
        
        screenshot.save(filepath)
        logger.info(f"Screenshot saved to: {filepath}")

"""
Tests for ScreenController.

Following TDD principles - these tests define expected behavior
for the screen capture functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
from PIL import Image
import io


class TestScreenControllerInit:
    """Tests for ScreenController initialization."""
    
    def test_init_uses_actual_screen_size_by_default(self):
        """Test that actual screen size is used when no dimensions provided."""
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController()
            
            assert controller.display_width == 1920
            assert controller.display_height == 1080
    
    def test_init_with_custom_dimensions(self):
        """Test that custom dimensions override actual screen size."""
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController(
                display_width=2560,
                display_height=1440
            )
            
            assert controller.display_width == 2560
            assert controller.display_height == 1440


class TestScreenControllerGetScreenSize:
    """Tests for ScreenController.get_screen_size method."""
    
    def test_get_screen_size_returns_tuple(self):
        """Test that get_screen_size returns actual screen dimensions."""
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController()
            size = controller.get_screen_size()
            
            assert size == (1920, 1080)
            assert isinstance(size, tuple)


class TestScreenControllerCaptureScreenshot:
    """Tests for ScreenController.capture_screenshot method."""
    
    def test_capture_screenshot_calls_pyautogui(self):
        """Test that capture_screenshot uses pyautogui.screenshot."""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (1920, 1080)
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=mock_image) as mock_screenshot:
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                result = controller.capture_screenshot()
                
                mock_screenshot.assert_called_once()
                assert result == mock_image
    
    def test_capture_screenshot_with_region(self):
        """Test that region parameter is passed to pyautogui."""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (100, 100)
        region = (0, 0, 100, 100)
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=mock_image) as mock_screenshot:
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                controller.capture_screenshot(region=region)
                
                mock_screenshot.assert_called_once_with(region=region)
    
    def test_capture_screenshot_stores_last_screenshot(self):
        """Test that last screenshot is stored."""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (1920, 1080)
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=mock_image):
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                controller.capture_screenshot()
                
                assert controller.get_last_screenshot() == mock_image


class TestScreenControllerScreenshotToBase64:
    """Tests for ScreenController.screenshot_to_base64 method."""
    
    def test_screenshot_to_base64_returns_string(self):
        """Test that screenshot_to_base64 returns a non-empty string."""
        # Create a real small image for testing
        test_image = Image.new('RGB', (10, 10), color='white')
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=test_image):
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                result = controller.screenshot_to_base64()
                
                assert isinstance(result, str)
                assert len(result) > 0
    
    def test_screenshot_to_base64_is_valid_base64(self):
        """Test that the result is valid base64."""
        test_image = Image.new('RGB', (10, 10), color='red')
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=test_image):
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                result = controller.screenshot_to_base64()
                
                # Should not raise an exception
                decoded = base64.b64decode(result)
                assert len(decoded) > 0
    
    def test_screenshot_to_base64_with_existing_image(self):
        """Test that existing image can be converted."""
        test_image = Image.new('RGB', (10, 10), color='blue')
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController()
            result = controller.screenshot_to_base64(screenshot=test_image)
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_screenshot_to_base64_captures_new_if_none_provided(self):
        """Test that new screenshot is captured if none provided."""
        test_image = Image.new('RGB', (10, 10), color='green')
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=test_image) as mock_screenshot:
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                controller.screenshot_to_base64()
                
                mock_screenshot.assert_called_once()


class TestScreenControllerSaveScreenshot:
    """Tests for ScreenController.save_screenshot method."""
    
    def test_save_screenshot_raises_if_no_screenshot(self):
        """Test that ValueError is raised if no screenshot available."""
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController()
            
            with pytest.raises(ValueError, match="No screenshot available"):
                controller.save_screenshot("test.png")
    
    def test_save_screenshot_uses_last_screenshot(self):
        """Test that last screenshot is used when none provided."""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (1920, 1080)
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.screenshot', return_value=mock_image):
                from src.screen.screen_controller import ScreenController
                
                controller = ScreenController()
                controller.capture_screenshot()
                controller.save_screenshot("test.png")
                
                mock_image.save.assert_called_once_with("test.png")
    
    def test_save_screenshot_with_provided_image(self):
        """Test that provided image is saved."""
        mock_image = MagicMock(spec=Image.Image)
        
        with patch('pyautogui.size', return_value=(1920, 1080)):
            from src.screen.screen_controller import ScreenController
            
            controller = ScreenController()
            controller.save_screenshot("test.png", screenshot=mock_image)
            
            mock_image.save.assert_called_once_with("test.png")

"""
Tests for ActionHandler.

Following TDD principles - these tests define expected behavior
for the action execution functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestActionHandlerInit:
    """Tests for ActionHandler initialization."""
    
    def test_init_with_default_dimensions(self):
        """Test that default dimensions are set."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler()
            
            assert handler.display_width == 1920
            assert handler.display_height == 1080
    
    def test_init_with_custom_dimensions(self):
        """Test that custom dimensions are accepted."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=2560, display_height=1440)
            
            assert handler.display_width == 2560
            assert handler.display_height == 1440


class TestActionHandlerValidateCoordinates:
    """Tests for ActionHandler.validate_coordinates method."""
    
    def test_validate_coordinates_returns_valid_coords(self):
        """Test that valid coordinates are returned unchanged."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=1920, display_height=1080)
            x, y = handler.validate_coordinates(500, 300)
            
            assert x == 500
            assert y == 300
    
    def test_validate_coordinates_clamps_negative_x(self):
        """Test that negative X is clamped to 0."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=1920, display_height=1080)
            x, y = handler.validate_coordinates(-100, 300)
            
            assert x == 0
            assert y == 300
    
    def test_validate_coordinates_clamps_negative_y(self):
        """Test that negative Y is clamped to 0."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=1920, display_height=1080)
            x, y = handler.validate_coordinates(500, -50)
            
            assert x == 500
            assert y == 0
    
    def test_validate_coordinates_clamps_x_over_max(self):
        """Test that X over max is clamped."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=1920, display_height=1080)
            x, y = handler.validate_coordinates(2000, 300)
            
            assert x == 1919  # display_width - 1
            assert y == 300
    
    def test_validate_coordinates_clamps_y_over_max(self):
        """Test that Y over max is clamped."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler(display_width=1920, display_height=1080)
            x, y = handler.validate_coordinates(500, 1200)
            
            assert x == 500
            assert y == 1079  # display_height - 1


class TestActionHandlerClick:
    """Tests for ActionHandler.click method."""
    
    def test_click_calls_pyautogui_click(self):
        """Test that click uses pyautogui.click."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.click') as mock_click:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.click(500, 300)
                
                mock_click.assert_called_once_with(500, 300, button='left', clicks=1)
    
    def test_click_with_right_button(self):
        """Test right-click functionality."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.click') as mock_click:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.click(500, 300, button='right')
                
                mock_click.assert_called_once_with(500, 300, button='right', clicks=1)
    
    def test_click_validates_coordinates(self):
        """Test that coordinates are validated before clicking."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.click') as mock_click:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler(display_width=1920, display_height=1080)
                handler.click(2000, 1200)  # Out of bounds
                
                # Should be clamped
                mock_click.assert_called_once_with(1919, 1079, button='left', clicks=1)


class TestActionHandlerDoubleClick:
    """Tests for ActionHandler.double_click method."""
    
    def test_double_click_calls_pyautogui_doubleClick(self):
        """Test that double_click uses pyautogui.doubleClick."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.doubleClick') as mock_dbl_click:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.double_click(500, 300)
                
                mock_dbl_click.assert_called_once_with(500, 300, button='left')


class TestActionHandlerTypeText:
    """Tests for ActionHandler.type_text method."""
    
    def test_type_text_calls_pyautogui_write(self):
        """Test that type_text uses pyautogui.write."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.write') as mock_write:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.type_text("Hello, world!")
                
                mock_write.assert_called_once_with("Hello, world!", interval=0.02)
    
    def test_type_text_with_custom_interval(self):
        """Test that custom interval is used."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.write') as mock_write:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.type_text("Test", interval=0.1)
                
                mock_write.assert_called_once_with("Test", interval=0.1)


class TestActionHandlerPressKey:
    """Tests for ActionHandler.press_key method."""
    
    def test_press_key_calls_pyautogui_press(self):
        """Test that press_key uses pyautogui.press."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.press') as mock_press:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.press_key("enter")
                
                mock_press.assert_called_once_with("enter")
    
    def test_press_key_maps_special_keys(self):
        """Test that special keys are mapped correctly."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.press') as mock_press:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.press_key("esc")
                
                mock_press.assert_called_once_with("escape")


class TestActionHandlerHotkey:
    """Tests for ActionHandler.hotkey method."""
    
    def test_hotkey_calls_pyautogui_hotkey(self):
        """Test that hotkey uses pyautogui.hotkey."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.hotkey') as mock_hotkey:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.hotkey("ctrl", "c")
                
                mock_hotkey.assert_called_once_with("ctrl", "c")
    
    def test_hotkey_maps_keys(self):
        """Test that keys are mapped in hotkey."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.hotkey') as mock_hotkey:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.hotkey("ctrl", "shift", "esc")
                
                mock_hotkey.assert_called_once_with("ctrl", "shift", "escape")


class TestActionHandlerScroll:
    """Tests for ActionHandler.scroll method."""
    
    def test_scroll_calls_pyautogui_scroll(self):
        """Test that scroll uses pyautogui.scroll."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.moveTo'):
                with patch('pyautogui.scroll') as mock_scroll:
                    from src.actions.action_handler import ActionHandler
                    
                    handler = ActionHandler()
                    handler.scroll(500, 300, clicks=3, direction="down")
                    
                    mock_scroll.assert_called_once_with(-3)
    
    def test_scroll_up_uses_positive_clicks(self):
        """Test that scrolling up uses positive clicks."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.moveTo'):
                with patch('pyautogui.scroll') as mock_scroll:
                    from src.actions.action_handler import ActionHandler
                    
                    handler = ActionHandler()
                    handler.scroll(500, 300, clicks=3, direction="up")
                    
                    mock_scroll.assert_called_once_with(3)


class TestActionHandlerWait:
    """Tests for ActionHandler.wait method."""
    
    def test_wait_sleeps_for_duration(self):
        """Test that wait sleeps for specified milliseconds."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('time.sleep') as mock_sleep:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                handler.wait(1000)
                
                mock_sleep.assert_called_once_with(1.0)


class TestActionHandlerExecuteAction:
    """Tests for ActionHandler.execute_action method."""
    
    def test_execute_action_click(self):
        """Test executing a click action from API response."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.click') as mock_click:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                action = {
                    "type": "click",
                    "x": 500,
                    "y": 300,
                    "button": "left"
                }
                
                handler.execute_action(action)
                
                mock_click.assert_called_once()
    
    def test_execute_action_type(self):
        """Test executing a type action from API response."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.write') as mock_write:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                action = {
                    "type": "type",
                    "text": "Hello, world!"
                }
                
                handler.execute_action(action)
                
                mock_write.assert_called_once()
    
    def test_execute_action_screenshot_does_nothing(self):
        """Test that screenshot action doesn't execute anything."""
        with patch('pyautogui.FAILSAFE', True):
            from src.actions.action_handler import ActionHandler
            
            handler = ActionHandler()
            action = {"type": "screenshot"}
            
            # Should not raise any exceptions
            handler.execute_action(action)
    
    def test_execute_action_keypress_single(self):
        """Test executing a single keypress action."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.press') as mock_press:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                action = {
                    "type": "keypress",
                    "keys": ["enter"]
                }
                
                handler.execute_action(action)
                
                mock_press.assert_called_once()
    
    def test_execute_action_keypress_multiple(self):
        """Test executing a keypress action with multiple keys."""
        with patch('pyautogui.FAILSAFE', True):
            with patch('pyautogui.hotkey') as mock_hotkey:
                from src.actions.action_handler import ActionHandler
                
                handler = ActionHandler()
                action = {
                    "type": "keypress",
                    "keys": ["ctrl", "s"]
                }
                
                handler.execute_action(action)
                
                mock_hotkey.assert_called_once()

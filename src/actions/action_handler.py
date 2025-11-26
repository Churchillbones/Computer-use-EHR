"""
Action handler for mouse and keyboard control.

Provides functionality to execute actions returned by the Computer Use API,
including clicks, typing, scrolling, and key presses.
"""

import logging
import time
from typing import Tuple, Optional, List

import pyautogui

logger = logging.getLogger(__name__)

# Disable pyautogui fail-safe warning but keep it enabled
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Small pause between actions


class ActionHandler:
    """
    Handler for executing mouse and keyboard actions.
    
    Translates Computer Use API actions into pyautogui commands
    and executes them safely with coordinate validation.
    
    Attributes:
        display_width: Maximum X coordinate.
        display_height: Maximum Y coordinate.
    
    Example:
        >>> handler = ActionHandler(display_width=1920, display_height=1080)
        >>> handler.click(500, 300)
        >>> handler.type_text("Hello, world!")
    """
    
    # Key mapping for special keys
    KEY_MAPPING = {
        "/": "slash",
        "\\": "backslash",
        "alt": "alt",
        "arrowdown": "down",
        "arrowleft": "left",
        "arrowright": "right",
        "arrowup": "up",
        "backspace": "backspace",
        "ctrl": "ctrl",
        "control": "ctrl",
        "delete": "delete",
        "enter": "enter",
        "return": "enter",
        "esc": "escape",
        "escape": "escape",
        "shift": "shift",
        "space": "space",
        "tab": "tab",
        "win": "win",
        "cmd": "win",
        "super": "win",
        "meta": "win",
        "option": "alt",
    }
    
    def __init__(
        self,
        display_width: int = 1920,
        display_height: int = 1080
    ) -> None:
        """
        Initialize the action handler.
        
        Args:
            display_width: Maximum X coordinate for validation.
            display_height: Maximum Y coordinate for validation.
        """
        self._display_width = display_width
        self._display_height = display_height
        
        logger.info(
            f"ActionHandler initialized with bounds: "
            f"{display_width}x{display_height}"
        )
    
    @property
    def display_width(self) -> int:
        """Get the display width."""
        return self._display_width
    
    @property
    def display_height(self) -> int:
        """Get the display height."""
        return self._display_height
    
    def validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """
        Validate and clamp coordinates to display bounds.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
        
        Returns:
            Tuple of validated (x, y) coordinates.
        """
        validated_x = max(0, min(x, self._display_width - 1))
        validated_y = max(0, min(y, self._display_height - 1))
        
        if validated_x != x or validated_y != y:
            logger.warning(
                f"Coordinates clamped from ({x}, {y}) to ({validated_x}, {validated_y})"
            )
        
        return validated_x, validated_y
    
    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1
    ) -> None:
        """
        Perform a mouse click at the specified coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            button: Mouse button ("left", "right", "middle").
            clicks: Number of clicks.
        """
        x, y = self.validate_coordinates(x, y)
        
        logger.info(f"Clicking at ({x}, {y}) with {button} button, {clicks} click(s)")
        
        # Handle special button types from Computer Use API
        if button == "back":
            pyautogui.hotkey("alt", "left")
            return
        elif button == "forward":
            pyautogui.hotkey("alt", "right")
            return
        elif button == "wheel":
            # Wheel button typically means scroll
            self.scroll(x, y, clicks=3)
            return
        
        # Map button to pyautogui format
        button_map = {"left": "left", "right": "right", "middle": "middle"}
        button = button_map.get(button.lower(), "left")
        
        pyautogui.click(x, y, button=button, clicks=clicks)
    
    def double_click(self, x: int, y: int, button: str = "left") -> None:
        """
        Perform a double-click at the specified coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            button: Mouse button ("left", "right", "middle").
        """
        x, y = self.validate_coordinates(x, y)
        
        logger.info(f"Double-clicking at ({x}, {y})")
        
        pyautogui.doubleClick(x, y, button=button)
    
    def move_to(self, x: int, y: int, duration: float = 0.25) -> None:
        """
        Move the mouse to the specified coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            duration: Time in seconds for the movement.
        """
        x, y = self.validate_coordinates(x, y)
        
        logger.info(f"Moving mouse to ({x}, {y})")
        
        pyautogui.moveTo(x, y, duration=duration)
    
    def type_text(self, text: str, interval: float = 0.02) -> None:
        """
        Type text using the keyboard.
        
        Args:
            text: Text to type.
            interval: Time between each keystroke in seconds.
        """
        logger.info(f"Typing text: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        pyautogui.write(text, interval=interval)
    
    def press_key(self, key: str) -> None:
        """
        Press a single key.
        
        Args:
            key: Key to press (e.g., "enter", "tab", "escape").
        """
        # Map key name if needed
        mapped_key = self.KEY_MAPPING.get(key.lower(), key.lower())
        
        logger.info(f"Pressing key: {mapped_key}")
        
        pyautogui.press(mapped_key)
    
    def hotkey(self, *keys: str) -> None:
        """
        Press a hotkey combination.
        
        Args:
            *keys: Keys to press together (e.g., "ctrl", "c" for Ctrl+C).
        """
        # Map all keys
        mapped_keys = [self.KEY_MAPPING.get(k.lower(), k.lower()) for k in keys]
        
        logger.info(f"Pressing hotkey: {'+'.join(mapped_keys)}")
        
        pyautogui.hotkey(*mapped_keys)
    
    def key_down(self, key: str) -> None:
        """
        Press and hold a key down.
        
        Args:
            key: Key to hold down.
        """
        mapped_key = self.KEY_MAPPING.get(key.lower(), key.lower())
        
        logger.info(f"Key down: {mapped_key}")
        
        pyautogui.keyDown(mapped_key)
    
    def key_up(self, key: str) -> None:
        """
        Release a held key.
        
        Args:
            key: Key to release.
        """
        mapped_key = self.KEY_MAPPING.get(key.lower(), key.lower())
        
        logger.info(f"Key up: {mapped_key}")
        
        pyautogui.keyUp(mapped_key)
    
    def scroll(
        self,
        x: int,
        y: int,
        clicks: int = 3,
        direction: str = "down"
    ) -> None:
        """
        Scroll the mouse wheel.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            clicks: Number of scroll clicks.
            direction: Scroll direction ("up" or "down").
        """
        x, y = self.validate_coordinates(x, y)
        
        # Move to position first
        pyautogui.moveTo(x, y)
        
        # Negative clicks for down, positive for up
        scroll_amount = clicks if direction == "up" else -clicks
        
        logger.info(f"Scrolling at ({x}, {y}): {scroll_amount} clicks")
        
        pyautogui.scroll(scroll_amount)
    
    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: str = "left"
    ) -> None:
        """
        Drag from one point to another.
        
        Args:
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            end_x: Ending X coordinate.
            end_y: Ending Y coordinate.
            duration: Time for the drag operation.
            button: Mouse button to use.
        """
        start_x, start_y = self.validate_coordinates(start_x, start_y)
        end_x, end_y = self.validate_coordinates(end_x, end_y)
        
        logger.info(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        pyautogui.moveTo(start_x, start_y)
        pyautogui.drag(
            end_x - start_x,
            end_y - start_y,
            duration=duration,
            button=button
        )
    
    def wait(self, milliseconds: int) -> None:
        """
        Wait for a specified duration.
        
        Args:
            milliseconds: Time to wait in milliseconds.
        """
        seconds = milliseconds / 1000.0
        
        logger.info(f"Waiting for {milliseconds}ms")
        
        time.sleep(seconds)
    
    def execute_action(self, action: dict) -> None:
        """
        Execute an action from the Computer Use API response.
        
        Args:
            action: Action dictionary from API response.
        
        Raises:
            ValueError: If action type is not recognized.
        """
        action_type = action.get("type", "").lower()
        
        logger.info(f"Executing action: {action_type}")
        
        if action_type == "click":
            self.click(
                x=action.get("x", 0),
                y=action.get("y", 0),
                button=action.get("button", "left")
            )
        
        elif action_type == "double_click":
            self.double_click(
                x=action.get("x", 0),
                y=action.get("y", 0)
            )
        
        elif action_type == "type":
            self.type_text(action.get("text", ""))
        
        elif action_type == "keypress":
            keys = action.get("keys", [])
            if len(keys) == 1:
                self.press_key(keys[0])
            elif len(keys) > 1:
                self.hotkey(*keys)
        
        elif action_type == "scroll":
            scroll_y = action.get("scroll_y", 0)
            direction = "up" if scroll_y < 0 else "down"
            self.scroll(
                x=action.get("x", 0),
                y=action.get("y", 0),
                clicks=abs(scroll_y) // 100 or 3,  # Convert pixels to clicks
                direction=direction
            )
        
        elif action_type == "move":
            self.move_to(
                x=action.get("x", 0),
                y=action.get("y", 0)
            )
        
        elif action_type == "drag":
            # Drag uses path or start/end coordinates
            path = action.get("path", [])
            if len(path) >= 2:
                start = path[0]
                end = path[-1]
                self.drag(
                    start_x=start.get("x", 0),
                    start_y=start.get("y", 0),
                    end_x=end.get("x", 0),
                    end_y=end.get("y", 0)
                )
        
        elif action_type == "wait":
            self.wait(action.get("ms", 1000))
        
        elif action_type == "screenshot":
            # Screenshot action doesn't require execution
            logger.info("Screenshot action - no execution needed")
        
        else:
            logger.warning(f"Unrecognized action type: {action_type}")

"""
Demo: GPT-4o Vision + Function Calling for Computer Automation
Opens Notepad and types "Happy Thanksgiving" using AI-driven screen analysis.

This demo uses:
- GPT-4o vision to analyze screenshots
- Function calling to execute mouse/keyboard actions
- pyautogui for actual screen interaction
"""

import os
import sys
import json
import time
import base64
import subprocess
import logging
import requests
import urllib3
from io import BytesIO
from typing import Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.screen.screen_controller import ScreenController
from src.actions.action_handler import ActionHandler

# Suppress SSL warnings for VA internal endpoints
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-4o"
MAX_ITERATIONS = 15
VERIFY_SSL = False  # VA internal endpoints use internal CA


# =============================================================================
# FUNCTION DEFINITIONS FOR OPENAI TOOLS
# =============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at x,y coordinates on screen. Use this to click buttons, text fields, menu items, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
                    "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
                    "button": {"type": "string", "enum": ["left", "right"], "default": "left", "description": "Mouse button to click"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "double_click",
            "description": "Double-click at x,y coordinates. Use for opening files, selecting words, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text using keyboard. The text will be typed character by character.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a single keyboard key. Examples: enter, tab, escape, backspace, delete, up, down, left, right, f1-f12",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press (e.g., 'enter', 'tab', 'escape')"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a keyboard shortcut/combination. Examples: ctrl+s (save), ctrl+v (paste), alt+f4 (close), win+r (run dialog)",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys to press together, e.g., ['ctrl', 's'] for Ctrl+S"
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait for a specified number of seconds. Use when waiting for windows to open, pages to load, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Number of seconds to wait", "default": 1}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Signal that the task has been completed successfully. Call this when the goal has been achieved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Brief summary of what was accomplished"}
                },
                "required": ["summary"]
            }
        }
    }
]


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a computer automation agent that can see the screen and control the mouse/keyboard.

Your goal is to complete the user's task by analyzing screenshots and executing actions.

IMPORTANT GUIDELINES:
1. Look carefully at the screenshot to understand the current state
2. Execute ONE action at a time, then wait for the next screenshot
3. Click on visible UI elements (buttons, text fields, menus) to interact with them
4. When you need to type, first click on the text field to focus it
5. Use keyboard shortcuts when appropriate (e.g., Win+R to open Run dialog)
6. If something doesn't work, try an alternative approach
7. Call task_complete when the goal has been achieved

SCREEN COORDINATES:
- The screenshot shows the full screen
- Coordinates (0,0) are at the top-left corner
- X increases going right, Y increases going down
- Click at the CENTER of buttons/elements for best results

CURRENT TASK: Open Notepad and type "Happy Thanksgiving"

STRATEGY:
1. Press Win+R to open Run dialog
2. Type "notepad" in the Run dialog
3. Press Enter to launch Notepad
4. Wait for Notepad to open
5. Type "Happy Thanksgiving" in the Notepad window
6. Call task_complete"""


# =============================================================================
# VISION CLIENT
# =============================================================================

class GPT4OVisionClient:
    """Client for GPT-4o with vision and function calling."""
    
    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.messages = []
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def reset_conversation(self):
        """Clear conversation history."""
        self.messages = []
    
    def send_with_vision(
        self,
        text: str,
        screenshot_base64: str,
        tools: list,
        system_prompt: str = None
    ) -> dict:
        """
        Send a message with a screenshot and get a response.
        
        Args:
            text: User message/task description
            screenshot_base64: Base64 encoded screenshot
            tools: List of function definitions
            system_prompt: Optional system prompt
        
        Returns:
            API response dict
        """
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        messages.extend(self.messages)
        
        # Add current message with screenshot
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"}
                }
            ]
        }
        messages.append(user_message)
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 1000
        }
        
        # Send request
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=60,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Store assistant response in history
        assistant_message = result["choices"][0]["message"]
        self.messages.append(user_message)
        self.messages.append(assistant_message)
        
        return result
    
    def send_function_result(
        self,
        tool_call_id: str,
        function_name: str,
        result: str,
        screenshot_base64: str,
        tools: list,
        system_prompt: str = None
    ) -> dict:
        """
        Send the result of a function call back to the model.
        
        Args:
            tool_call_id: ID of the tool call being responded to
            function_name: Name of the function that was called
            result: Result of the function execution
            screenshot_base64: Updated screenshot after action
            tools: List of function definitions
            system_prompt: Optional system prompt
        
        Returns:
            API response dict
        """
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        messages.extend(self.messages)
        
        # Add function result
        function_message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result
        }
        messages.append(function_message)
        
        # Add follow-up with new screenshot
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Action executed. Here is the updated screen. What should I do next?"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"}
                }
            ]
        }
        messages.append(user_message)
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 1000
        }
        
        # Send request
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=60,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        
        result_data = response.json()
        
        # Store in history
        self.messages.append(function_message)
        assistant_message = result_data["choices"][0]["message"]
        self.messages.append(user_message)
        self.messages.append(assistant_message)
        
        return result_data


# =============================================================================
# ACTION EXECUTOR
# =============================================================================

def execute_function_call(
    action_handler: ActionHandler,
    function_name: str,
    arguments: dict
) -> tuple[bool, str, bool]:
    """
    Execute a function call using the ActionHandler.
    
    Args:
        action_handler: ActionHandler instance
        function_name: Name of function to execute
        arguments: Function arguments
    
    Returns:
        Tuple of (success, result_message, is_task_complete)
    """
    is_complete = False
    
    try:
        if function_name == "click":
            x = arguments.get("x", 0)
            y = arguments.get("y", 0)
            button = arguments.get("button", "left")
            action_handler.click(x, y, button=button)
            result = f"Clicked at ({x}, {y}) with {button} button"
            
        elif function_name == "double_click":
            x = arguments.get("x", 0)
            y = arguments.get("y", 0)
            action_handler.double_click(x, y)
            result = f"Double-clicked at ({x}, {y})"
            
        elif function_name == "type_text":
            text = arguments.get("text", "")
            action_handler.type_text(text)
            result = f"Typed: {text}"
            
        elif function_name == "press_key":
            key = arguments.get("key", "")
            action_handler.press_key(key)
            result = f"Pressed key: {key}"
            
        elif function_name == "hotkey":
            keys = arguments.get("keys", [])
            action_handler.hotkey(*keys)
            result = f"Pressed hotkey: {'+'.join(keys)}"
            
        elif function_name == "wait":
            seconds = arguments.get("seconds", 1)
            # ActionHandler.wait() expects milliseconds
            action_handler.wait(int(seconds * 1000))
            result = f"Waited {seconds} seconds"
            
        elif function_name == "task_complete":
            summary = arguments.get("summary", "Task completed")
            is_complete = True
            result = f"Task complete: {summary}"
            
        else:
            result = f"Unknown function: {function_name}"
            return False, result, False
        
        logger.info(f"✅ {result}")
        return True, result, is_complete
        
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg, False


# =============================================================================
# MAIN DEMO
# =============================================================================

def run_demo():
    """Run the Notepad automation demo."""
    
    print("\n" + "="*60)
    print("🤖 GPT-4o Vision + Function Calling Demo")
    print("📝 Task: Open Notepad and type 'Happy Thanksgiving'")
    print("="*60 + "\n")
    
    # Initialize components
    screen = ScreenController()
    actions = ActionHandler()
    client = GPT4OVisionClient(BASE_URL, API_KEY, MODEL)
    
    # Get screen size for reference
    width, height = screen.get_screen_size()
    logger.info(f"Screen size: {width}x{height}")
    
    # Initial task message
    task_message = "Please complete this task: Open Notepad and type 'Happy Thanksgiving'"
    
    # Take initial screenshot
    logger.info("Taking initial screenshot...")
    screenshot = screen.capture_screenshot()
    screenshot_base64 = screen.screenshot_to_base64(screenshot)
    
    # Main automation loop
    iteration = 0
    task_complete = False
    last_tool_call = None
    
    while iteration < MAX_ITERATIONS and not task_complete:
        iteration += 1
        print(f"\n{'─'*40}")
        print(f"🔄 Iteration {iteration}/{MAX_ITERATIONS}")
        print(f"{'─'*40}")
        
        try:
            # Send to GPT-4o
            if last_tool_call is None:
                # Initial request
                logger.info("Sending screenshot to GPT-4o...")
                response = client.send_with_vision(
                    task_message,
                    screenshot_base64,
                    TOOLS,
                    SYSTEM_PROMPT
                )
            else:
                # Follow-up after function execution
                logger.info("Sending updated screenshot after action...")
                response = client.send_function_result(
                    last_tool_call["id"],
                    last_tool_call["function"]["name"],
                    last_tool_call["result"],
                    screenshot_base64,
                    TOOLS,
                    SYSTEM_PROMPT
                )
            
            # Parse response
            message = response["choices"][0]["message"]
            
            # Check for text content (reasoning)
            if message.get("content"):
                print(f"\n💭 Model thinking: {message['content'][:200]}...")
            
            # Check for tool calls
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("No tool calls in response. Model may be done or stuck.")
                # Check if there's a completion message
                if message.get("content") and "complete" in message["content"].lower():
                    task_complete = True
                continue
            
            # Execute the first tool call
            tool_call = tool_calls[0]
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            print(f"\n🎯 Action: {function_name}")
            print(f"   Args: {json.dumps(arguments)}")
            
            # Execute the action
            success, result, task_complete = execute_function_call(
                actions, function_name, arguments
            )
            
            # Store for next iteration
            last_tool_call = {
                "id": tool_call["id"],
                "function": tool_call["function"],
                "result": result
            }
            
            if task_complete:
                print("\n" + "="*60)
                print("🎉 TASK COMPLETED SUCCESSFULLY!")
                print("="*60)
                break
            
            # Wait a moment for screen to update
            time.sleep(0.5)
            
            # Take new screenshot
            logger.info("Capturing updated screenshot...")
            screenshot = screen.capture_screenshot()
            screenshot_base64 = screen.screenshot_to_base64(screenshot)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            break
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse function arguments: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if not task_complete:
        print("\n" + "="*60)
        print("⚠️  Task did not complete within max iterations")
        print("="*60)
    
    return task_complete


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("\n🚀 Starting GPT-4o Vision Demo...")
    print("   This demo will open Notepad and type 'Happy Thanksgiving'")
    print("   using AI-powered screen analysis and automation.\n")
    
    input("Press Enter to begin (make sure your screen is visible)...")
    
    success = run_demo()
    
    print("\n" + "─"*60)
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo did not complete. Check the logs above.")
    print("─"*60 + "\n")

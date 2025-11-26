"""
Demo: GPT-5 Vision + Function Calling for Computer Automation
Opens Notepad and types "Happy Thanksgiving" using GPT-5.

Note: GPT-5 requires 'max_completion_tokens' instead of 'max_tokens'
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.screen.screen_controller import ScreenController
from src.actions.action_handler import ActionHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-5"  # Using GPT-5!


def send_to_gpt5(messages: list, tools: list = None) -> dict:
    """Send request to GPT-5 and return response."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_completion_tokens": 4096  # GPT-5 uses max_completion_tokens
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
        verify=False
    )
    response.raise_for_status()
    return response.json()


def take_screenshot_base64() -> str:
    """Take a screenshot and return as base64."""
    screen = ScreenController()
    screenshot = screen.capture_screenshot()
    return screen.screenshot_to_base64(screenshot)


# Function tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at x,y coordinates on the screen",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
                    "y": {"type": "integer", "description": "Y coordinate (pixels from top)"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text using the keyboard",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to type"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key (enter, tab, escape, etc)",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a keyboard shortcut like ctrl+s, win+r, alt+f4",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys to press together, e.g., ['ctrl', 's']"
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Signal that the task has been completed successfully",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "What was accomplished"}
                },
                "required": ["summary"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a computer automation agent using GPT-5. You can see the screen and control the mouse/keyboard.

IMPORTANT:
1. Analyze screenshots carefully before acting
2. Execute ONE action at a time
3. Click to focus before typing
4. Use hotkeys like Win+R to open Run dialog
5. If Notepad opens with existing text, press Ctrl+N to create a new blank tab first
6. Call task_complete when finished

TASK: Open Notepad and type "Happy Thanksgiving"

STRATEGY:
1. Press Win+R to open Run dialog
2. Type "notepad" and press Enter
3. Wait for Notepad to open
4. If there is existing text in Notepad, press Ctrl+N to open a new tab
5. Click in the blank text area
6. Type "Happy Thanksgiving"
7. Call task_complete"""


def execute_function(actions: ActionHandler, name: str, args: dict) -> tuple[bool, str, bool]:
    """Execute a function call. Returns (success, message, is_complete)."""
    is_complete = False
    
    try:
        if name == "click":
            actions.click(args["x"], args["y"])
            return True, f"Clicked at ({args['x']}, {args['y']})", False
        
        elif name == "type_text":
            actions.type_text(args["text"])
            return True, f"Typed: {args['text']}", False
        
        elif name == "press_key":
            actions.press_key(args["key"])
            return True, f"Pressed: {args['key']}", False
        
        elif name == "hotkey":
            actions.hotkey(*args["keys"])
            return True, f"Hotkey: {'+'.join(args['keys'])}", False
        
        elif name == "task_complete":
            return True, f"Complete: {args.get('summary', 'Done')}", True
        
        else:
            return False, f"Unknown function: {name}", False
            
    except Exception as e:
        return False, f"Error: {e}", False


def run_gpt5_demo():
    """Run the GPT-5 powered demo."""
    
    print("\n" + "="*60)
    print("🧠 GPT-5 Vision + Function Calling Demo")
    print("📝 Task: Open Notepad and type 'Happy Thanksgiving'")
    print("="*60 + "\n")
    
    actions = ActionHandler()
    screen = ScreenController()
    
    width, height = screen.get_screen_size()
    logger.info(f"Screen: {width}x{height}")
    
    # Conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Take initial screenshot
    logger.info("Taking initial screenshot...")
    screenshot_b64 = take_screenshot_base64()
    
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": "Here is the current screen. Please start the task: Open Notepad and type 'Happy Thanksgiving'. What is your first action?"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
        ]
    })
    
    max_iterations = 15
    iteration = 0
    task_complete = False
    
    while iteration < max_iterations and not task_complete:
        iteration += 1
        print(f"\n{'─'*40}")
        print(f"🔄 Iteration {iteration}/{max_iterations}")
        print(f"{'─'*40}")
        
        try:
            # Send to GPT-5
            logger.info("Sending to GPT-5...")
            response = send_to_gpt5(messages, TOOLS)
            
            msg = response["choices"][0]["message"]
            messages.append(msg)  # Add assistant response to history
            
            # Check for content
            if msg.get("content"):
                print(f"\n💭 GPT-5: {msg['content'][:200]}...")
            
            # Check for tool calls
            tool_calls = msg.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("No tool calls. GPT-5 may be thinking or stuck.")
                # Add a nudge
                messages.append({
                    "role": "user",
                    "content": "Please use one of the available functions to proceed with the task."
                })
                continue
            
            # Execute first tool call
            tc = tool_calls[0]
            func_name = tc["function"]["name"]
            func_args = json.loads(tc["function"]["arguments"])
            
            print(f"\n🎯 Action: {func_name}")
            print(f"   Args: {json.dumps(func_args)}")
            
            success, result_msg, task_complete = execute_function(actions, func_name, func_args)
            
            if success:
                logger.info(f"✅ {result_msg}")
            else:
                logger.error(f"❌ {result_msg}")
            
            if task_complete:
                print("\n" + "="*60)
                print("🎉 TASK COMPLETED!")
                print("="*60)
                break
            
            # Add tool result
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_msg
            })
            
            # Wait and take new screenshot
            time.sleep(1)
            logger.info("Taking new screenshot...")
            screenshot_b64 = take_screenshot_base64()
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Action completed: {result_msg}. Here is the updated screen. What's next?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ]
            })
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if not task_complete:
        print("\n⚠️  Task did not complete within max iterations")
    
    return task_complete


if __name__ == "__main__":
    print("\n🚀 Starting GPT-5 Vision Demo...")
    print("   This uses GPT-5 (not GPT-4o) for computer automation\n")
    
    input("Press Enter to begin...")
    
    success = run_gpt5_demo()
    
    print("\n" + "─"*60)
    if success:
        print("✅ Demo completed successfully with GPT-5!")
    else:
        print("❌ Demo did not complete.")
    print("─"*60 + "\n")

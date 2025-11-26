"""
Demo: GPT-5 Vision + Function Calling for Computer Automation
Opens Notepad and types "Happy Thanksgiving" using GPT-5.

NOTE: This Azure endpoint (spd-dev-openai-std-apim.azure-api.us) accepts Chat Completions
format on the /responses endpoint. The standard Responses API format (with 'input' instead
of 'messages') returns "Unsupported data type" error.

GPT-5 capabilities used:
- Vision (screenshot analysis)
- Function/tool calling
- max_completion_tokens parameter
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
ENDPOINT = "responses"  # Using Responses API endpoint

# Speed settings
SCREENSHOT_DELAY = 0.15  # Seconds to wait after action before screenshot (reduced for speed)
API_TIMEOUT = 45  # API timeout in seconds


# Reusable session for connection pooling (faster subsequent requests)
_session = None

def get_session() -> requests.Session:
    """Get or create a reusable session with connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.verify = False
        _session.headers.update({
            "api-key": API_KEY,
            "Content-Type": "application/json"
        })
    return _session


def send_to_gpt5(messages: list, tools: list = None) -> dict:
    """Send request to GPT-5 using the Responses API endpoint.
    
    Note: This endpoint accepts Chat Completions format (messages array).
    Uses connection pooling for faster subsequent requests.
    
    Args:
        messages: List of message objects with role and content
        tools: List of tool definitions
    
    Returns:
        API response as dict
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_completion_tokens": 4096  # Higher limit for vision + creative responses
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"  # Allow model flexibility
    
    session = get_session()
    response = session.post(
        f"{BASE_URL}/{ENDPOINT}",
        json=payload,
        timeout=API_TIMEOUT
    )
    
    if response.status_code != 200:
        logger.error(f"API Error {response.status_code}: {response.text}")
    response.raise_for_status()
    return response.json()


# Global screen controller (reuse to avoid re-initialization)
_screen_controller = None

def take_screenshot_base64() -> str:
    """Take a screenshot, resize it for efficiency, and return as base64."""
    global _screen_controller
    if _screen_controller is None:
        _screen_controller = ScreenController()
    screenshot = _screen_controller.capture_screenshot()
    
    # Resize to reduce token usage (half size is still readable)
    width, height = screenshot.size
    screenshot = screenshot.resize((width // 2, height // 2))
    
    # Convert to JPEG for smaller size
    buffer = BytesIO()
    screenshot.save(buffer, format="JPEG", quality=70)
    return base64.b64encode(buffer.getvalue()).decode()


# Function tools - Chat Completions format (nested under 'function')
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

SYSTEM_PROMPT = """You are a computer automation agent that MUST use function calls to control the computer.

IMPORTANT: You MUST call functions - do NOT just respond with text!

Notepad is open. Your task:
1. FIRST: Call click() to click in the white text area of Notepad (center of screen works)
2. THEN: Call type_text() to type something creative (a haiku, joke, ASCII art, fun fact - your choice!)
3. FINALLY: Call task_complete() when done

RESPOND ONLY WITH FUNCTION CALLS. Pick something fun to type!"""


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


def open_notepad_and_type(actions: ActionHandler, text: str):
    """Open Notepad and type text - fully automated, no GPT-5 needed."""
    print("📋 Opening Notepad...")
    
    # Step 1: Win+R
    actions.hotkey("win", "r")
    time.sleep(0.4)
    
    # Step 2: Type notepad
    actions.type_text("notepad")
    time.sleep(0.15)
    
    # Step 3: Press Enter
    actions.press_key("enter")
    time.sleep(0.8)  # Wait for Notepad to open
    
    print("✅ Notepad opened!")
    
    # Step 4: Type the message (Notepad opens with focus, no click needed)
    print(f"⌨️  Typing: {text}")
    actions.type_text(text)
    
    print("✅ Done!")


def run_gpt5_demo():
    """Run the demo - now fully automated for speed."""
    
    print("\n" + "="*60)
    print("🚀 Fast Notepad Demo (No API calls needed!)")
    print("📝 Task: Open Notepad and type 'Happy Thanksgiving'")
    print("="*60 + "\n")
    
    actions = ActionHandler()
    
    # Fully automated - no GPT-5 API calls needed!
    start_time = time.time()
    
    open_notepad_and_type(actions, "Happy Thanksgiving")
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print(f"🎉 TASK COMPLETED in {elapsed:.1f} seconds!")
    print("="*60)
    
    return True


# Keep GPT-5 version available for complex tasks
def run_gpt5_vision_demo():
    """Run the GPT-5 vision-powered demo - GPT-5 decides what to create!"""
    
    print("\n" + "="*60)
    print("🧠 GPT-5 Creative Notepad Demo")
    print("📝 GPT-5 will decide what to write - let's see what it creates!")
    print("="*60 + "\n")
    
    actions = ActionHandler()
    screen = ScreenController()
    
    width, height = screen.get_screen_size()
    logger.info(f"Screen: {width}x{height}")
    
    # FAST: Pre-execute steps 1-3 (open Notepad) without GPT-5
    print("📋 Opening Notepad (automated)...")
    actions.hotkey("win", "r")
    time.sleep(0.5)
    actions.type_text("notepad")
    time.sleep(0.2)
    actions.press_key("enter")
    time.sleep(1.0)
    print("✅ Notepad opened!")
    
    # Now use GPT-5 only for vision-based clicking and typing
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Take screenshot after Notepad is open
    screenshot_b64 = take_screenshot_base64()
    
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": "Notepad is open and ready! Look at the screen and create something interesting. What will you make?"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
        ]
    })
    
    max_iterations = 8  # Fewer iterations needed now
    iteration = 0
    task_complete = False
    
    while iteration < max_iterations and not task_complete:
        iteration += 1
        print(f"\n{'─'*40}")
        print(f"🔄 Iteration {iteration}/{max_iterations}")
        print(f"{'─'*40}")
        
        try:
            # Send to GPT-5
            response = send_to_gpt5(messages, TOOLS)
            
            msg = response["choices"][0]["message"]
            messages.append(msg)  # Add assistant response to history
            
            # Check for content
            if msg.get("content"):
                print(f"\n💭 GPT-5: {msg['content'][:200]}...")
            
            # Check for tool calls
            tool_calls = msg.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("No tool calls. Nudging...")
                # Take a fresh screenshot and nudge
                screenshot_b64 = take_screenshot_base64()
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Use a function now. Current screen:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                    ]
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
            
            # Wait and take new screenshot (reduced delay for speed)
            time.sleep(SCREENSHOT_DELAY)
            screenshot_b64 = take_screenshot_base64()
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Done: {result_msg}. Next?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ]
            })
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if not task_complete:
        print("\n⚠️  Task did not complete within max iterations")
    
    return task_complete


if __name__ == "__main__":
    print("\n🚀 GPT-5 Computer Use Demo")
    print("   Choose mode:")
    print("   1. GPT-5 Creative (GPT-5 decides what to write!) - default")
    print("   2. Fast scripted (no API calls)\n")
    
    choice = input("Press Enter for GPT-5 creative mode, or '2' for fast scripted: ").strip()
    
    if choice == "2":
        success = run_gpt5_demo()
    else:
        success = run_gpt5_vision_demo()
    
    print("\n" + "─"*60)
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo did not complete.")
    print("─"*60 + "\n")

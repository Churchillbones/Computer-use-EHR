"""
Demo: GPT-5 Vision + Function Calling (OPTIMIZED for speed)
Opens Notepad and types "Happy Thanksgiving" using GPT-5.
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
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.screen.screen_controller import ScreenController
from src.actions.action_handler import ActionHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-5"

# Speed optimizations
SCREENSHOT_SCALE = 0.5  # Resize to 50% (960x540 instead of 1920x1080)
JPEG_QUALITY = 70       # Use JPEG compression
MAX_TOKENS = 1024       # Reduced from 4096
REQUEST_TIMEOUT = 45    # Reduced timeout


def take_screenshot_optimized() -> str:
    """Take a compressed screenshot for faster processing."""
    import pyautogui
    
    # Capture screenshot
    screenshot = pyautogui.screenshot()
    
    # Resize for faster processing
    new_width = int(screenshot.width * SCREENSHOT_SCALE)
    new_height = int(screenshot.height * SCREENSHOT_SCALE)
    screenshot = screenshot.resize((new_width, new_height), Image.LANCZOS)
    
    # Convert to JPEG (much smaller than PNG)
    buffer = BytesIO()
    screenshot.convert('RGB').save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def send_to_gpt5(messages: list, tools: list = None) -> dict:
    """Send optimized request to GPT-5."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_completion_tokens": MAX_TOKENS,
        # Note: GPT-5 only supports temperature=1 (default)
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
        verify=False
    )
    response.raise_for_status()
    return response.json()


# Minimal function tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at x,y (coordinates are for 960x540 scaled screen)",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press hotkey like ['win','r'] or ['ctrl','s']",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press key (enter, tab, escape)",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Task complete",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# Minimal system prompt
SYSTEM_PROMPT = """Computer automation agent. Screen is scaled to 960x540.
Task: Open Notepad (Win+R, type notepad, Enter). If Notepad opens with existing text, press Ctrl+N for new tab. Then type "Happy Thanksgiving" in the empty area, then call done.
Execute ONE action per turn. Coordinates must be scaled (multiply real coords by 0.5)."""


def execute_function(actions: ActionHandler, name: str, args: dict) -> tuple[bool, str, bool]:
    """Execute function. Scale coordinates back to real screen."""
    try:
        if name == "click":
            # Scale coordinates back to full screen
            x = int(args["x"] / SCREENSHOT_SCALE)
            y = int(args["y"] / SCREENSHOT_SCALE)
            actions.click(x, y)
            return True, f"Clicked ({x},{y})", False
        
        elif name == "type_text":
            actions.type_text(args["text"])
            return True, f"Typed: {args['text']}", False
        
        elif name == "hotkey":
            actions.hotkey(*args["keys"])
            return True, f"Hotkey: {'+'.join(args['keys'])}", False
        
        elif name == "press_key":
            actions.press_key(args["key"])
            return True, f"Key: {args['key']}", False
        
        elif name == "done":
            return True, "Done", True
        
        return False, f"Unknown: {name}", False
            
    except Exception as e:
        return False, str(e), False


def run_fast_demo():
    """Run optimized GPT-5 demo."""
    
    print("\n" + "="*60)
    print("⚡ GPT-5 FAST Demo (Optimized)")
    print("📝 Open Notepad → Type 'Happy Thanksgiving'")
    print("="*60 + "\n")
    
    start_time = time.time()
    
    actions = ActionHandler()
    
    # Single message approach - no conversation history bloat
    max_iterations = 10
    task_complete = False
    
    for i in range(max_iterations):
        iter_start = time.time()
        print(f"\n[{i+1}/{max_iterations}] ", end="", flush=True)
        
        # Take optimized screenshot
        screenshot_b64 = take_screenshot_optimized()
        print(f"📷", end=" ", flush=True)
        
        # Build fresh message each time (no history accumulation)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Current screen. Execute next action:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"}}
                ]
            }
        ]
        
        # Send to GPT-5
        response = send_to_gpt5(messages, TOOLS)
        print(f"🤖", end=" ", flush=True)
        
        msg = response["choices"][0]["message"]
        tool_calls = msg.get("tool_calls", [])
        
        if not tool_calls:
            print("⚠️ No action")
            continue
        
        tc = tool_calls[0]
        func_name = tc["function"]["name"]
        func_args = json.loads(tc["function"]["arguments"])
        
        success, result, task_complete = execute_function(actions, func_name, func_args)
        
        iter_time = time.time() - iter_start
        print(f"→ {func_name} {func_args} ({iter_time:.1f}s)")
        
        if task_complete:
            break
        
        # Brief pause for screen to update
        time.sleep(0.3)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*60)
    if task_complete:
        print(f"🎉 COMPLETED in {total_time:.1f}s ({i+1} iterations)")
    else:
        print(f"⚠️ Did not complete in {max_iterations} iterations")
    print("="*60 + "\n")
    
    return task_complete


if __name__ == "__main__":
    print("\n⚡ GPT-5 FAST Demo")
    print("   Optimizations: 50% scaled JPEG, minimal prompts, no history\n")
    
    input("Press Enter to start...")
    
    run_fast_demo()

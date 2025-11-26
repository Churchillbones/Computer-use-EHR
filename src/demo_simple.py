"""
Demo: GPT-4o Vision + Function Calling for Computer Automation (Simplified)
Opens Notepad and types "Happy Thanksgiving" using AI-driven screen analysis.

This is a simplified, more deterministic version.
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


# Configuration
BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-4o"


def send_to_gpt4o(messages: list, tools: list = None) -> dict:
    """Send request to GPT-4o and return response."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1000
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
        verify=False
    )
    response.raise_for_status()
    return response.json()


def take_screenshot_base64() -> str:
    """Take a screenshot and return as base64."""
    screen = ScreenController()
    screenshot = screen.capture_screenshot()
    return screen.screenshot_to_base64(screenshot)


# Function tools for the AI
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at x,y coordinates",
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
            "name": "task_complete",
            "description": "Task is done",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def run_simple_demo():
    """Run a simple, step-by-step demo."""
    
    print("\n" + "="*60)
    print("🤖 GPT-4o Vision Demo - Simple Version")
    print("📝 Opening Notepad and typing 'Happy Thanksgiving'")
    print("="*60 + "\n")
    
    actions = ActionHandler()
    
    # Step 1: Open Notepad directly using subprocess
    print("Step 1: Opening Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2)  # Wait for Notepad to open
    print("   ✅ Notepad launched\n")
    
    # Step 1.5: Check if Notepad has existing content, if so open new tab
    print("Step 1.5: Checking if Notepad is blank...")
    screenshot_b64 = take_screenshot_base64()
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Look at the Notepad window. Is there any existing text in it? Answer only YES or NO."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                }
            ]
        }
    ]
    
    response = send_to_gpt4o(messages)
    has_content = response["choices"][0]["message"]["content"].strip().upper()
    
    if "YES" in has_content:
        print("   ⚠️ Notepad has existing content, opening new tab...")
        actions.hotkey("ctrl", "n")
        time.sleep(1)
        print("   ✅ New tab opened\n")
    else:
        print("   ✅ Notepad is blank\n")
    
    # Step 2: Take a screenshot and ask GPT-4o where to click
    print("Step 2: Analyzing screen with GPT-4o vision...")
    screenshot_b64 = take_screenshot_base64()
    
    messages = [
        {
            "role": "system",
            "content": "You are helping automate a computer. Look at the screenshot and identify where to click to type in Notepad. The white text area in Notepad is where we need to type."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I just opened Notepad. Look at the screenshot and tell me the exact x,y coordinates of the CENTER of the white text area where I should click to start typing. Just give me the coordinates as JSON: {\"x\": number, \"y\": number}"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                }
            ]
        }
    ]
    
    response = send_to_gpt4o(messages)
    content = response["choices"][0]["message"]["content"]
    print(f"   GPT-4o response: {content}")
    
    # Try to parse coordinates from response
    try:
        # Look for JSON in the response
        import re
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            coords = json.loads(json_match.group())
            x, y = coords.get("x", 960), coords.get("y", 540)
        else:
            # Default to center of screen if parsing fails
            x, y = 960, 400
        print(f"   ✅ Click target: ({x}, {y})\n")
    except Exception as e:
        print(f"   ⚠️ Could not parse coordinates, using default. Error: {e}")
        x, y = 960, 400
    
    # Step 3: Click in Notepad
    print("Step 3: Clicking in Notepad text area...")
    actions.click(x, y)
    time.sleep(0.5)
    print("   ✅ Clicked\n")
    
    # Step 4: Type the message
    print("Step 4: Typing 'Happy Thanksgiving'...")
    actions.type_text("Happy Thanksgiving")
    time.sleep(0.5)
    print("   ✅ Typed message\n")
    
    # Step 5: Verify with screenshot
    print("Step 5: Verifying with GPT-4o vision...")
    screenshot_b64 = take_screenshot_base64()
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Look at this screenshot. Is there a Notepad window with the text 'Happy Thanksgiving' visible? Answer YES or NO and briefly explain what you see."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                }
            ]
        }
    ]
    
    response = send_to_gpt4o(messages)
    verification = response["choices"][0]["message"]["content"]
    print(f"   GPT-4o verification: {verification}\n")
    
    # Done
    print("="*60)
    if "YES" in verification.upper() or "HAPPY THANKSGIVING" in verification.upper():
        print("🎉 SUCCESS! Task completed!")
    else:
        print("⚠️ Task may not have completed as expected. Check the screen.")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🚀 Starting Simple GPT-4o Vision Demo...")
    print("   This will open Notepad and type 'Happy Thanksgiving'\n")
    
    input("Press Enter to begin...")
    
    run_simple_demo()

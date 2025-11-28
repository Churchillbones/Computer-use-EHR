"""
GPT-4.1 Computer Use Demo
=========================
Uses the fastest available model (gpt-4.1) for computer automation.
GPT-4.1 has a 1M token context window and 32K output - optimized for speed!

Based on Microsoft Azure OpenAI documentation:
https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/models#gpt-41-series
"""
import time
import json
import base64
import logging
import subprocess
from io import BytesIO
from typing import Optional

import requests
import urllib3

# Disable SSL warnings for VA network
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# Configuration - GPT-4.1 (fastest model!)
# ============================================================
BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-4.1"  # Fastest model with vision + tools
ENDPOINT = "responses"

# GPT-4.1 specific parameters
MAX_COMPLETION_TOKENS = 4096  # GPT-4.1 supports up to 32K output
TEMPERATURE = 0.7  # GPT-4.1 supports temperature (unlike reasoning models)

# System prompt optimized for GPT-4.1's strengths
SYSTEM_PROMPT = """You are a computer automation agent using GPT-4.1.

You MUST use function calls to interact with the computer. Do NOT respond with text only.

Notepad is open. Your task:
1. Call click() to click in the Notepad text area (white area in center)
2. Call type_text() to type something creative - a haiku, joke, ASCII art, or fun fact
3. Call task_complete() when finished

BE CREATIVE! Show what you can do. Use the tools now."""

# ============================================================
# Tool Definitions (Chat Completions format for your APIM)
# ============================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (0-1920)"},
                    "y": {"type": "integer", "description": "Y coordinate (0-1080)"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text with keyboard. Supports newlines.",
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
            "description": "Press a keyboard key",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name (enter, tab, escape, etc.)"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Call when the task is finished",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Summary of what was done"}
                },
                "required": ["summary"]
            }
        }
    }
]

# ============================================================
# Screen Controller
# ============================================================
from src.screen.screen_controller import ScreenController
from src.actions.action_handler import ActionHandler

_screen_controller: Optional[ScreenController] = None
_action_handler: Optional[ActionHandler] = None


def get_action_handler() -> ActionHandler:
    global _action_handler
    if _action_handler is None:
        _action_handler = ActionHandler()
    return _action_handler


def take_screenshot_base64() -> str:
    """Take screenshot, resize for efficiency, return as base64 JPEG."""
    global _screen_controller
    if _screen_controller is None:
        _screen_controller = ScreenController()
    
    screenshot = _screen_controller.capture_screenshot()
    
    # Resize to half for faster API response
    width, height = screenshot.size
    screenshot = screenshot.resize((width // 2, height // 2))
    
    # JPEG for smaller size
    buffer = BytesIO()
    screenshot.save(buffer, format="JPEG", quality=70)
    return base64.b64encode(buffer.getvalue()).decode()


# ============================================================
# GPT-4.1 API Call
# ============================================================
def call_gpt41(messages: list) -> dict:
    """Call GPT-4.1 via your Azure APIM endpoint."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "temperature": TEMPERATURE,  # GPT-4.1 supports this!
    }
    
    url = f"{BASE_URL}/{ENDPOINT}"
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        logger.error(f"Response: {response.text[:500]}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}


# ============================================================
# Action Execution
# ============================================================
def execute_action(name: str, args: dict) -> str:
    """Execute a tool action and return result."""
    handler = get_action_handler()
    
    if name == "click":
        handler.click(args["x"], args["y"])
        return f"Clicked at ({args['x']}, {args['y']})"
    
    elif name == "type_text":
        handler.type_text(args["text"])
        return f"Typed: {args['text'][:50]}..."
    
    elif name == "press_key":
        handler.press_key(args["key"])
        return f"Pressed: {args['key']}"
    
    elif name == "task_complete":
        logger.info(f"✅ Complete: {args['summary']}")
        return "TASK_COMPLETE"
    
    return f"Unknown action: {name}"


# ============================================================
# Main Agent Loop
# ============================================================
def run_agent(max_iterations: int = 8):
    """Run the GPT-4.1 agent loop."""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for i in range(max_iterations):
        print(f"\n{'─'*40}")
        print(f"🔄 Iteration {i+1}/{max_iterations}")
        print('─'*40)
        
        # Take screenshot
        img_b64 = take_screenshot_base64()
        
        # Build user message with image
        user_content = [
            {"type": "text", "text": "Here is the current screen. Take action."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
        messages.append({"role": "user", "content": user_content})
        
        # Call GPT-4.1
        start_time = time.time()
        response = call_gpt41(messages)
        api_time = time.time() - start_time
        
        if "error" in response:
            logger.error(f"API Error: {response['error']}")
            break
        
        # Parse response
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        # Add assistant response to history
        messages.append(message)
        
        if not tool_calls:
            content = message.get("content", "")
            logger.warning(f"No tool calls. Response: {content[:100]}")
            # Nudge the model
            messages.append({
                "role": "user", 
                "content": "You MUST use a tool. Call click(), type_text(), or task_complete() now."
            })
            continue
        
        # Execute tool calls
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name")
            args = json.loads(func.get("arguments", "{}"))
            
            print(f"\n🎯 Action: {name} ({api_time:.1f}s)")
            print(f"   Args: {json.dumps(args)}")
            
            result = execute_action(name, args)
            
            if result == "TASK_COMPLETE":
                print("\n" + "="*60)
                print("🎉 TASK COMPLETED!")
                print("="*60)
                return True
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result
            })
        
        time.sleep(0.5)  # Brief pause between iterations
    
    print("\n⚠️  Max iterations reached")
    return False


# ============================================================
# Demo Entry Point
# ============================================================
def open_notepad():
    """Open Notepad using Win+R."""
    handler = get_action_handler()
    print("📋 Opening Notepad...")
    handler.hotkey('win', 'r')
    time.sleep(0.5)
    handler.type_text("notepad")
    time.sleep(0.3)
    handler.press_key('enter')
    time.sleep(1.5)
    print("✅ Notepad opened!")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           GPT-4.1 Computer Use Demo                          ║
║                                                              ║
║  🚀 Using the FASTEST model available!                       ║
║  📊 1M token context | 32K output | Vision + Tools           ║
║  ⚡ ~2 second response times                                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("Choose mode:")
    print("  1. GPT-4.1 Creative (model decides what to write)")
    print("  2. Quick test (just verify API works)")
    print()
    choice = input("Enter choice (1/2) [1]: ").strip() or "1"
    
    if choice == "2":
        # Quick API test
        print("\n🔍 Testing GPT-4.1 API...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'GPT-4.1 is working!' in exactly those words."}
        ]
        
        # Simple test without tools
        headers = {"api-key": API_KEY, "Content-Type": "application/json"}
        payload = {
            "model": MODEL,
            "messages": messages,
            "max_completion_tokens": 50,
            "temperature": 0.7
        }
        
        start = time.time()
        r = requests.post(f"{BASE_URL}/{ENDPOINT}", json=payload, headers=headers, verify=False, timeout=30)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ Response ({elapsed:.1f}s): {content}")
        else:
            print(f"❌ Error {r.status_code}: {r.text[:200]}")
        return
    
    # Full demo
    print("\n" + "="*60)
    print("🧠 GPT-4.1 Creative Notepad Demo")
    print("📝 GPT-4.1 will decide what to write!")
    print("="*60)
    
    # Initialize
    handler = get_action_handler()
    logger.info(f"Screen: {handler.display_width}x{handler.display_height}")
    
    # Open Notepad
    open_notepad()
    
    # Run agent
    success = run_agent(max_iterations=8)
    
    print("\n" + "─"*60)
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo did not complete.")
    print("─"*60)


if __name__ == "__main__":
    main()

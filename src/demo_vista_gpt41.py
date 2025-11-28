"""
GPT-4.1 Vista CPRS EHR Automation Demo
======================================
Uses GPT-4.1 (fastest model) for Vista CPRS EHR automation.
GPT-4.1 has a 1M token context window and 32K output - optimized for speed!

Workflow:
1. Click "New Note" button
2. Double-click "Mh Rrtp Group Note" in list
3. Click "Templates" button
4. Click SCMI folder expand caret (►)
5. Double-click "SCMI" template
6. Right-click → "Save without Signature"
7. Task complete
"""
import time
import json
import base64
import logging
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
MAX_COMPLETION_TOKENS = 4096
TEMPERATURE = 0.7

# EHR Workflow Settings
MAX_ITERATIONS = 25  # More iterations for complex EHR workflow
ACTION_DELAY = 1.5   # Longer delay for EHR UI response

# System prompt for Vista CPRS automation
SYSTEM_PROMPT = """You are a computer automation agent using GPT-4.1. You can see the screen and control the mouse/keyboard to automate Vista CPRS (VA Electronic Health Record system).

CRITICAL RULES:
1. CAREFULLY ANALYZE each screenshot - look for EXACT text labels on buttons
2. VERIFY after each action - did the screen change as expected? If not, the click missed!
3. DO NOT assume an action worked - check the new screenshot to confirm
4. If a dialog didn't open or an item wasn't selected, try different coordinates
5. Read text labels exactly - find "New Note" text, not just click in the general area

TASK: Create a new SCMI progress note in Vista CPRS

KNOWN COORDINATES (verified by user):
- "New Note" button: x=242, y=974 (near bottom of screen!)
- The button is MUCH LOWER than you might expect - y=974, not y=677
- IMPORTANT: "New Note" requires DOUBLE-CLICK, not single click!

WORKFLOW STEPS:
1. DOUBLE-CLICK the "New Note" button at approximately (242, 974) - MUST be double-click!
2. VERIFY: A "Progress Note Properties" dialog should appear with a list of note types
3. DOUBLE-CLICK "MH RRTP GROUP NOTE" in the dialog list
4. VERIFY: The dialog should close and a note editing area appears
5. In the Templates tree on the left, find and DOUBLE-CLICK the "SCMI" template
6. VERIFY: Template content should appear in the note
7. RIGHT-CLICK in the note text area to open context menu
8. Click "Save without Signature" in the context menu
9. Call task_complete ONLY when the note is actually saved

IMPORTANT - VERIFICATION:
- After EVERY action, examine the new screenshot carefully
- If the expected result didn't happen, the coordinates were wrong
- Adjust and try again - don't proceed with the next step until current step succeeds

YOU MUST use function calls. Always verify the result before proceeding."""

# ============================================================
# Tool Definitions (Chat Completions format)
# ============================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click at x,y coordinates on the screen. Use button='right' for right-click context menus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
                    "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right"],
                        "description": "Mouse button to click. Default is 'left'. Use 'right' for context menus."
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "double_click",
            "description": "Double-click at x,y coordinates. Use this to select items in lists, open items, or activate templates.",
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
            "description": "Press a keyboard key (enter, tab, escape, up, down, etc)",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press (enter, tab, escape, up, down, left, right, etc)"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a keyboard shortcut like ctrl+s, ctrl+n, alt+f4",
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
            "name": "scroll",
            "description": "Scroll up or down at a position to find items in lists or tree views",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate to scroll at"},
                    "y": {"type": "integer", "description": "Y coordinate to scroll at"},
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "Scroll direction"
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of scroll clicks (default 3)"
                    }
                },
                "required": ["x", "y", "direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait for a specified time to let the UI respond",
            "parameters": {
                "type": "object",
                "properties": {
                    "milliseconds": {
                        "type": "integer",
                        "description": "Time to wait in milliseconds (e.g., 1000 = 1 second)"
                    }
                },
                "required": ["milliseconds"]
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


def get_screen_controller() -> ScreenController:
    global _screen_controller
    if _screen_controller is None:
        _screen_controller = ScreenController()
    return _screen_controller


def take_screenshot_base64() -> str:
    """Take screenshot and return as base64 PNG (full resolution for accuracy)."""
    screen = get_screen_controller()
    screenshot = screen.capture_screenshot()
    
    # Use full resolution PNG for better text reading
    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# ============================================================
# GPT-4.1 API Call
# ============================================================
def call_gpt41(messages: list) -> dict:
    """Call GPT-4.1 via Azure APIM endpoint."""
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
        "temperature": TEMPERATURE,
    }
    
    url = f"{BASE_URL}/{ENDPOINT}"
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=120)
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
def execute_action(name: str, args: dict) -> tuple[bool, str, bool]:
    """Execute an action and return (success, message, is_complete)."""
    handler = get_action_handler()
    is_complete = False
    
    try:
        if name == "click":
            button = args.get("button", "left")
            handler.click(args["x"], args["y"], button=button)
            button_desc = "Right-clicked" if button == "right" else "Clicked"
            return True, f"{button_desc} at ({args['x']}, {args['y']})", False
        
        elif name == "double_click":
            handler.double_click(args["x"], args["y"])
            return True, f"Double-clicked at ({args['x']}, {args['y']})", False
        
        elif name == "type_text":
            handler.type_text(args["text"])
            return True, f"Typed: {args['text'][:50]}...", False
        
        elif name == "press_key":
            handler.press_key(args["key"])
            return True, f"Pressed: {args['key']}", False
        
        elif name == "hotkey":
            handler.hotkey(*args["keys"])
            return True, f"Hotkey: {'+'.join(args['keys'])}", False
        
        elif name == "scroll":
            direction = args.get("direction", "down")
            clicks = args.get("clicks", 3)
            handler.scroll(args["x"], args["y"], clicks=clicks, direction=direction)
            return True, f"Scrolled {direction} {clicks} clicks at ({args['x']}, {args['y']})", False
        
        elif name == "wait":
            ms = args.get("milliseconds", 1000)
            handler.wait(ms)
            return True, f"Waited {ms}ms", False
        
        elif name == "task_complete":
            logger.info(f"✅ Complete: {args['summary']}")
            return True, f"Task Complete: {args.get('summary', 'Done')}", True
        
        else:
            return False, f"Unknown action: {name}", False
            
    except Exception as e:
        return False, f"Error executing {name}: {e}", False


# ============================================================
# Main Agent Loop
# ============================================================
def run_vista_cprs_workflow():
    """Run the GPT-4.1 Vista CPRS agent loop."""
    
    print("\n" + "="*70)
    print("🏥 Vista CPRS EHR Automation with GPT-4.1")
    print("📝 Task: Create SCMI Progress Note")
    print("🚀 Using the FASTEST model available!")
    print("="*70)
    print("\nWorkflow Steps:")
    print("  1. Click 'New Note'")
    print("  2. Double-click 'Mh Rrtp Group Note'")
    print("  3. Click 'Templates'")
    print("  4. Expand 'SCMI' folder")
    print("  5. Double-click 'SCMI' template")
    print("  6. Right-click → 'Save without Signature'")
    print("="*70 + "\n")
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Take initial screenshot
    logger.info("Taking initial screenshot of Vista CPRS...")
    img_b64 = take_screenshot_base64()
    
    # Build initial user message with screenshot
    user_content = [
        {
            "type": "text", 
            "text": """Here is the current Vista CPRS screen with a patient open. 

TASK: DOUBLE-CLICK the "New Note" button to start creating a note.

KNOWN INFO:
- The "New Note" button is at approximately x=242, y=974 (near bottom of screen)
- You MUST use double_click(), not click()

Call double_click() now with the coordinates for "New Note"."""
        },
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
    ]
    messages.append({"role": "user", "content": user_content})
    
    task_complete = False
    
    for i in range(MAX_ITERATIONS):
        print(f"\n{'─'*50}")
        print(f"🔄 Iteration {i+1}/{MAX_ITERATIONS}")
        print('─'*50)
        
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
        
        # Log GPT-4.1's analysis if present
        if message.get("content"):
            print(f"\n💭 GPT-4.1 Analysis:")
            content = message["content"]
            # Truncate long analysis for display
            if len(content) > 500:
                print(f"   {content[:500]}...")
            else:
                print(f"   {content}")
        
        if not tool_calls:
            logger.warning("No tool calls. Nudging model...")
            messages.append({
                "role": "user", 
                "content": "You MUST use a function to proceed. Call click(), double_click(), or another function now."
            })
            continue
        
        # Execute first tool call
        tc = tool_calls[0]
        func = tc.get("function", {})
        name = func.get("name")
        args = json.loads(func.get("arguments", "{}"))
        
        print(f"\n🎯 Action: {name} ({api_time:.1f}s)")
        print(f"   Args: {json.dumps(args)}")
        
        success, result_msg, task_complete = execute_action(name, args)
        
        if success:
            logger.info(f"✅ {result_msg}")
        else:
            logger.error(f"❌ {result_msg}")
        
        if task_complete:
            print("\n" + "="*70)
            print("🎉 VISTA CPRS WORKFLOW COMPLETED!")
            print(f"   {result_msg}")
            print("="*70)
            return True
        
        # Add tool result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result_msg
        })
        
        # Wait for UI to respond, then take new screenshot
        time.sleep(ACTION_DELAY)
        logger.info("Taking updated screenshot...")
        img_b64 = take_screenshot_base64()
        
        # Add new screenshot with context
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": f"""Action attempted: {result_msg}

IMPORTANT: Look at this NEW screenshot carefully.
1. Did the action WORK? Did something change on screen?
2. If a dialog should have opened, IS IT VISIBLE?
3. If an item should have been selected, IS IT HIGHLIGHTED?

If the expected result DID NOT happen, the click MISSED - try different coordinates.
If it worked, proceed to the next step.

What do you see? What should we do next?"""
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        })
    
    print(f"\n⚠️  Workflow did not complete within {MAX_ITERATIONS} iterations")
    print("   The note may be partially created. Check Vista CPRS manually.")
    return False


# ============================================================
# Demo Entry Point
# ============================================================
def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           GPT-4.1 Vista CPRS EHR Automation Demo                     ║
║                                                                      ║
║  🚀 Using the FASTEST model available!                               ║
║  📊 1M token context | 32K output | Vision + Tools                   ║
║  ⚡ ~2-3 second response times                                        ║
║  🏥 Task: Create SCMI Progress Note in Vista CPRS                    ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("Prerequisites:")
    print("  ✓ Vista CPRS is open")
    print("  ✓ A test patient is selected")
    print("  ✓ Notes tab is visible")
    print("\nThe script will automate:")
    print("  1. Creating a new note")
    print("  2. Selecting 'Mh Rrtp Group Note' type")
    print("  3. Applying the 'SCMI' template")
    print("  4. Saving without signature")
    print("="*70)
    
    input("\nPress Enter when Vista CPRS is ready...")
    
    # Initialize
    handler = get_action_handler()
    logger.info(f"Screen: {handler.display_width}x{handler.display_height}")
    
    # Run workflow
    success = run_vista_cprs_workflow()
    
    print("\n" + "─"*70)
    if success:
        print("✅ Vista CPRS workflow completed successfully!")
    else:
        print("❌ Workflow did not complete. Check Vista CPRS for partial progress.")
    print("─"*70 + "\n")


if __name__ == "__main__":
    main()

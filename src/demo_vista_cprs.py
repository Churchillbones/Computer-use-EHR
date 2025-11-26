"""
Demo: GPT-5 Vision + Function Calling for Vista CPRS EHR Automation
Creates a progress note using SCMI template in Vista CPRS.

Workflow:
1. Click "New Note" button
2. Double-click "Mh Rrtp Group Note" in list
3. Click "Templates" button
4. Click SCMI folder expand caret (►)
5. Double-click "SCMI" template
6. Right-click → "Save without Signature"
7. Task complete

Note: GPT-5 requires 'max_completion_tokens' instead of 'max_tokens'
"""

import os
import sys
import json
import time
import logging
import requests
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.screen.screen_controller import ScreenController
from src.actions.action_handler import ActionHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - GPT-5 Azure OpenAI
BASE_URL = "https://spd-dev-openai-std-apim.azure-api.us/openai/v1"
API_KEY = "9f3680b1c04548a0a0ef5b0eb65d8764"
MODEL = "gpt-5"

# EHR Workflow Settings
MAX_ITERATIONS = 25  # More iterations for complex EHR workflow
ACTION_DELAY = 1.5   # Longer delay for EHR UI response


def send_to_gpt5(messages: list, tools: list = None) -> dict:
    """Send request to GPT-5 and return response."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_completion_tokens": 4096  # GPT-5 uses max_completion_tokens, NOT max_tokens
        # Note: GPT-5 does not support custom 'temperature' parameter
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,  # Longer timeout for complex reasoning
        verify=False  # VA internal endpoint
    )
    response.raise_for_status()
    return response.json()


def take_screenshot_base64() -> str:
    """Take a screenshot and return as base64."""
    screen = ScreenController()
    screenshot = screen.capture_screenshot()
    return screen.screenshot_to_base64(screenshot)


# Function tools for Vista CPRS automation
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

SYSTEM_PROMPT = """You are a computer automation agent using GPT-5. You can see the screen and control the mouse/keyboard to automate Vista CPRS (VA Electronic Health Record system).

IMPORTANT RULES:
1. Analyze screenshots carefully before acting - look for buttons, lists, tree views
2. Execute ONE action at a time
3. Wait for UI to respond after each action
4. Use single-click for buttons
5. Use DOUBLE-CLICK to select items in lists (like note types in dialogs)
6. Use right-click to open context menus (for save options)
7. Learn from previous actions - the conversation history shows what worked
8. Call task_complete when the note has been saved

TASK: Create a new SCMI progress note in Vista CPRS

VISTA CPRS LAYOUT (1920x1080 screen):
- The "New Note" button is at the BOTTOM LEFT, approximately x=160, y=677 (small button, look carefully)
- It's ABOVE the tab bar (Cover Sheet, Problems, Meds, Orders, Notes tabs are around y=695)
- The "New Note" button text is small, located next to "Encounter" label
- When clicked, a "Progress Note Properties" dialog appears with a list of note types
- Templates panel on LEFT shows folders including "SCMI" which contains the "SCMI" template

WORKFLOW STEPS:
1. CLICK the "New Note" button (bottom left, around x=160, y=677 - ABOVE the tab bar)
2. A "Progress Note Properties" dialog will open with a list of note types
3. DOUBLE-CLICK "MH RRTP GROUP NOTE" in the list (usually near the top)
4. The dialog closes and you're now editing a note
5. In the Templates tree on the left, DOUBLE-CLICK the "SCMI" template inside the SCMI folder
6. RIGHT-CLICK in the note text area on the right side
7. Click "Save without Signature" in the context menu
8. Call task_complete with summary

COORDINATE TIPS:
- "New Note" button: approximately x=130-180, y=675-680 (NOT y=690+, that's the tab bar)
- Tab bar is at y=695+ (Cover Sheet, Problems, Meds, Orders, Notes)
- Note type list in dialog starts around y=185
- Template tree is in the left panel

REMEMBER: Look carefully at the screen. Be precise with Y coordinates - the New Note button is ABOVE the tab bar."""


def execute_function(actions: ActionHandler, name: str, args: dict) -> tuple[bool, str, bool]:
    """Execute a function call. Returns (success, message, is_complete)."""
    is_complete = False
    
    try:
        if name == "click":
            button = args.get("button", "left")
            actions.click(args["x"], args["y"], button=button)
            button_desc = "Right-clicked" if button == "right" else "Clicked"
            return True, f"{button_desc} at ({args['x']}, {args['y']})", False
        
        elif name == "double_click":
            actions.double_click(args["x"], args["y"])
            return True, f"Double-clicked at ({args['x']}, {args['y']})", False
        
        elif name == "type_text":
            actions.type_text(args["text"])
            return True, f"Typed: {args['text']}", False
        
        elif name == "press_key":
            actions.press_key(args["key"])
            return True, f"Pressed: {args['key']}", False
        
        elif name == "hotkey":
            actions.hotkey(*args["keys"])
            return True, f"Hotkey: {'+'.join(args['keys'])}", False
        
        elif name == "scroll":
            direction = args.get("direction", "down")
            clicks = args.get("clicks", 3)
            actions.scroll(args["x"], args["y"], clicks=clicks, direction=direction)
            return True, f"Scrolled {direction} {clicks} clicks at ({args['x']}, {args['y']})", False
        
        elif name == "wait":
            ms = args.get("milliseconds", 1000)
            actions.wait(ms)
            return True, f"Waited {ms}ms", False
        
        elif name == "task_complete":
            return True, f"Task Complete: {args.get('summary', 'Done')}", True
        
        else:
            return False, f"Unknown function: {name}", False
            
    except Exception as e:
        return False, f"Error executing {name}: {e}", False


def run_vista_cprs_workflow():
    """Run the Vista CPRS EHR automation workflow."""
    
    print("\n" + "="*70)
    print("🏥 Vista CPRS EHR Automation with GPT-5")
    print("📝 Task: Create SCMI Progress Note")
    print("="*70)
    print("\nWorkflow Steps:")
    print("  1. Click 'New Note'")
    print("  2. Double-click 'Mh Rrtp Group Note'")
    print("  3. Click 'Templates'")
    print("  4. Expand 'SCMI' folder")
    print("  5. Double-click 'SCMI' template")
    print("  6. Right-click → 'Save without Signature'")
    print("="*70 + "\n")
    
    actions = ActionHandler()
    screen = ScreenController()
    
    width, height = screen.get_screen_size()
    logger.info(f"Screen resolution: {width}x{height}")
    
    # Conversation history for GPT-5 context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Take initial screenshot
    logger.info("Taking initial screenshot of Vista CPRS...")
    screenshot_b64 = take_screenshot_base64()
    
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text", 
                "text": """Here is the current Vista CPRS screen with a patient open. 

BEFORE you take any action, please:
1. Describe what you see on the screen (main areas, panels, buttons visible)
2. Identify where the "New Note" button is located (look at the bottom left area)
3. Then call the click function with the coordinates for "New Note"

Start the workflow to create a new SCMI progress note."""
            },
            {
                "type": "image_url", 
                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
            }
        ]
    })
    
    iteration = 0
    task_complete = False
    
    while iteration < MAX_ITERATIONS and not task_complete:
        iteration += 1
        print(f"\n{'─'*50}")
        print(f"🔄 Iteration {iteration}/{MAX_ITERATIONS}")
        print(f"{'─'*50}")
        
        try:
            # Send to GPT-5
            logger.info("Sending to GPT-5...")
            response = send_to_gpt5(messages, TOOLS)
            
            msg = response["choices"][0]["message"]
            messages.append(msg)  # Add assistant response to history
            
            # Log full reasoning/content from GPT-5
            if msg.get("content"):
                print(f"\n💭 GPT-5 Analysis:")
                print(f"   {msg['content']}")
            
            # Check for tool calls
            tool_calls = msg.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("No tool calls returned. Prompting GPT-5 to take action.")
                messages.append({
                    "role": "user",
                    "content": "Please use one of the available functions to proceed with the Vista CPRS workflow. What action should we take next?"
                })
                continue
            
            # Execute first tool call
            tc = tool_calls[0]
            func_name = tc["function"]["name"]
            func_args = json.loads(tc["function"]["arguments"])
            
            print(f"\n🎯 Action: {func_name}")
            print(f"   Args: {json.dumps(func_args, indent=2)}")
            
            success, result_msg, task_complete = execute_function(actions, func_name, func_args)
            
            if success:
                logger.info(f"✅ {result_msg}")
            else:
                logger.error(f"❌ {result_msg}")
            
            if task_complete:
                print("\n" + "="*70)
                print("🎉 VISTA CPRS WORKFLOW COMPLETED!")
                print(f"   {result_msg}")
                print("="*70)
                break
            
            # Add tool result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_msg
            })
            
            # Wait for UI to respond, then take new screenshot
            time.sleep(ACTION_DELAY)
            logger.info("Taking updated screenshot...")
            screenshot_b64 = take_screenshot_base64()
            
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"Action completed: {result_msg}. Here is the updated Vista CPRS screen. What's the next step in the workflow?"
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                    }
                ]
            })
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API Error: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if not task_complete:
        print(f"\n⚠️  Workflow did not complete within {MAX_ITERATIONS} iterations")
        print("   The note may be partially created. Check Vista CPRS manually.")
    
    return task_complete


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Starting Vista CPRS EHR Automation with GPT-5")
    print("="*70)
    print("\nPrerequisites:")
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
    
    success = run_vista_cprs_workflow()
    
    print("\n" + "─"*70)
    if success:
        print("✅ Vista CPRS workflow completed successfully!")
    else:
        print("❌ Workflow did not complete. Check Vista CPRS for partial progress.")
    print("─"*70 + "\n")

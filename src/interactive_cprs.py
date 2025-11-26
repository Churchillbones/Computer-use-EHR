"""
Interactive Vista CPRS Assistant with Session Learning

A text-based REPL where you guide GPT-5 through Vista CPRS with natural language.
Sessions are auto-saved to JSON for review and agent improvement.

Usage:
    python -m src.interactive_cprs

Commands:
    - Natural language: "click on New Note", "double-click MH RRTP GROUP NOTE"
    - Direct: "click 160 677", "double_click 350 187"
    - Control: "screenshot", "undo", "help", "quit"

Sessions saved to: sessions/session_YYYYMMDD_HHMMSS.json
"""

import os
import sys
import json
import time
import logging
import requests
import urllib3
from datetime import datetime
from pathlib import Path

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

# Session storage
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class SessionLogger:
    """Logs all interactions to JSON for learning and improvement."""
    
    def __init__(self):
        SESSIONS_DIR.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = SESSIONS_DIR / f"session_{self.session_id}.json"
        self.session_data = {
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "model": MODEL,
            "interactions": [],
            "summary": {
                "total_interactions": 0,
                "successful_actions": 0,
                "failed_actions": 0,
                "user_corrections": 0
            }
        }
        self._save()
        logger.info(f"📁 Session logging to: {self.session_file}")
    
    def log_interaction(self, interaction: dict):
        """Log a single interaction."""
        interaction["timestamp"] = datetime.now().isoformat()
        interaction["interaction_number"] = len(self.session_data["interactions"]) + 1
        self.session_data["interactions"].append(interaction)
        self.session_data["summary"]["total_interactions"] += 1
        
        if interaction.get("action_success"):
            self.session_data["summary"]["successful_actions"] += 1
        elif interaction.get("action_success") is False:
            self.session_data["summary"]["failed_actions"] += 1
        
        if interaction.get("user_correction"):
            self.session_data["summary"]["user_corrections"] += 1
        
        self._save()
    
    def add_final_summary(self, notes: str = ""):
        """Add final session summary."""
        self.session_data["ended_at"] = datetime.now().isoformat()
        self.session_data["final_notes"] = notes
        self._save()
    
    def _save(self):
        """Save session to JSON file."""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)


class InteractiveCPRS:
    """Interactive Vista CPRS assistant with GPT-5."""
    
    SYSTEM_PROMPT = """You are an interactive Vista CPRS automation assistant. You help the user navigate Vista CPRS (VA Electronic Health Record) by analyzing screenshots and executing actions.

YOUR ROLE:
- Analyze the current screen when asked
- Find UI elements the user describes (buttons, list items, text fields)
- Provide precise coordinates for clicking
- Execute actions when instructed
- Learn from user corrections

AVAILABLE ACTIONS (respond with JSON):
{
    "action": "click",
    "x": <int>,
    "y": <int>,
    "button": "left" or "right",
    "reasoning": "why this location"
}

{
    "action": "double_click",
    "x": <int>,
    "y": <int>,
    "reasoning": "why this location"
}

{
    "action": "type_text",
    "text": "<text to type>",
    "reasoning": "why typing this"
}

{
    "action": "hotkey",
    "keys": ["ctrl", "s"],
    "reasoning": "why this shortcut"
}

{
    "action": "scroll",
    "x": <int>,
    "y": <int>,
    "direction": "up" or "down",
    "clicks": <int>,
    "reasoning": "why scrolling"
}

{
    "action": "wait",
    "milliseconds": <int>,
    "reasoning": "why waiting"
}

{
    "action": "describe",
    "description": "<what you see on screen>",
    "elements": [{"name": "element name", "location": "approximate area", "coordinates": [x, y]}]
}

VISTA CPRS UI KNOWLEDGE:
- Screen resolution: 1920x1080
- "New Note" button: bottom-left area, below Templates panel, approximately x=130-180, y=675-680
- Tab bar (Cover Sheet, Problems, Meds, Orders, Notes): y=695+
- Templates panel: left side, contains folders like SCMI
- Note type dialog: appears after clicking New Note, has scrollable list
- To select items in lists: use double_click
- To open context menus: use right-click (button="right")
- Save menu appears on right-click, select "Save without Signature"

RESPONSE FORMAT:
Always respond with valid JSON. If you need to describe the screen first, use the "describe" action.
If the user gives a correction, acknowledge it and learn for future actions.

BE PRECISE: Vista CPRS has small UI elements. Analyze carefully before providing coordinates."""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "execute_action",
                "description": "Execute a screen action based on user request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["click", "double_click", "type_text", "hotkey", "scroll", "wait", "describe"],
                            "description": "The action to perform"
                        },
                        "x": {"type": "integer", "description": "X coordinate for click/scroll actions"},
                        "y": {"type": "integer", "description": "Y coordinate for click/scroll actions"},
                        "button": {"type": "string", "enum": ["left", "right"], "description": "Mouse button for click"},
                        "text": {"type": "string", "description": "Text to type"},
                        "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys for hotkey"},
                        "direction": {"type": "string", "enum": ["up", "down"], "description": "Scroll direction"},
                        "clicks": {"type": "integer", "description": "Number of scroll clicks"},
                        "milliseconds": {"type": "integer", "description": "Wait time in ms"},
                        "description": {"type": "string", "description": "Screen description"},
                        "elements": {"type": "array", "description": "UI elements found"},
                        "reasoning": {"type": "string", "description": "Why this action"}
                    },
                    "required": ["action"]
                }
            }
        }
    ]

    def __init__(self):
        self.actions = ActionHandler()
        self.screen = ScreenController()
        self.session = SessionLogger()
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        self.last_action = None
        self.action_history = []
        
    def send_to_gpt5(self, user_input: str, include_screenshot: bool = True) -> dict:
        """Send message to GPT-5 with optional screenshot."""
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json"
        }
        
        # Build user message
        content = []
        content.append({"type": "text", "text": user_input})
        
        if include_screenshot:
            screenshot_b64 = self.screen.screenshot_to_base64(self.screen.capture_screenshot())
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
            })
        
        self.messages.append({"role": "user", "content": content})
        
        payload = {
            "model": MODEL,
            "messages": self.messages,
            "max_completion_tokens": 4096
            # No tools - GPT-5 will respond with JSON in content
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
            verify=False
        )
        response.raise_for_status()
        return response.json()
    
    def execute_action(self, action_data: dict) -> tuple[bool, str]:
        """Execute an action and return (success, message)."""
        action = action_data.get("action")
        reasoning = action_data.get("reasoning", "")
        
        try:
            if action == "click":
                x, y = action_data["x"], action_data["y"]
                button = action_data.get("button", "left")
                self.actions.click(x, y, button=button)
                self.last_action = {"type": "click", "x": x, "y": y, "button": button}
                return True, f"{'Right-' if button == 'right' else ''}Clicked at ({x}, {y})"
            
            elif action == "double_click":
                x, y = action_data["x"], action_data["y"]
                self.actions.double_click(x, y)
                self.last_action = {"type": "double_click", "x": x, "y": y}
                return True, f"Double-clicked at ({x}, {y})"
            
            elif action == "type_text":
                text = action_data["text"]
                self.actions.type_text(text)
                self.last_action = {"type": "type_text", "text": text}
                return True, f"Typed: {text}"
            
            elif action == "hotkey":
                keys = action_data["keys"]
                self.actions.hotkey(*keys)
                self.last_action = {"type": "hotkey", "keys": keys}
                return True, f"Pressed: {'+'.join(keys)}"
            
            elif action == "scroll":
                x, y = action_data["x"], action_data["y"]
                direction = action_data.get("direction", "down")
                clicks = action_data.get("clicks", 3)
                self.actions.scroll(x, y, clicks=clicks, direction=direction)
                self.last_action = {"type": "scroll", "x": x, "y": y, "direction": direction}
                return True, f"Scrolled {direction} at ({x}, {y})"
            
            elif action == "wait":
                ms = action_data.get("milliseconds", 1000)
                self.actions.wait(ms)
                return True, f"Waited {ms}ms"
            
            elif action == "describe":
                desc = action_data.get("description", "No description")
                elements = action_data.get("elements", [])
                return True, f"Screen: {desc}\nElements: {json.dumps(elements, indent=2)}"
            
            else:
                return False, f"Unknown action: {action}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def process_response(self, response: dict) -> tuple[str, dict | None]:
        """Process GPT-5 response and extract action if present."""
        msg = response["choices"][0]["message"]
        self.messages.append(msg)
        
        content = msg.get("content", "")
        action_data = None
        
        # Try to extract JSON from content
        if content and "{" in content and "}" in content:
            try:
                # Find JSON block in response
                start = content.index("{")
                # Find matching closing brace
                brace_count = 0
                end = start
                for i, char in enumerate(content[start:], start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                
                json_str = content[start:end]
                action_data = json.loads(json_str)
                if "action" not in action_data:
                    action_data = None
            except (json.JSONDecodeError, ValueError):
                pass
        
        return content, action_data
    
    def handle_direct_command(self, user_input: str) -> tuple[bool, str] | None:
        """Handle direct commands like 'click 160 677'. Returns None if not a direct command."""
        parts = user_input.lower().strip().split()
        
        if not parts:
            return None
        
        cmd = parts[0]
        
        if cmd == "click" and len(parts) >= 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                button = parts[3] if len(parts) > 3 else "left"
                self.actions.click(x, y, button=button)
                self.last_action = {"type": "click", "x": x, "y": y, "button": button}
                return True, f"Direct click at ({x}, {y})"
            except ValueError:
                return None
        
        elif cmd == "double_click" and len(parts) >= 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                self.actions.double_click(x, y)
                self.last_action = {"type": "double_click", "x": x, "y": y}
                return True, f"Direct double-click at ({x}, {y})"
            except ValueError:
                return None
        
        elif cmd == "screenshot":
            # Just take and show screenshot info
            screenshot = self.screen.capture_screenshot()
            return True, f"Screenshot taken: {screenshot.size[0]}x{screenshot.size[1]}"
        
        elif cmd == "help":
            help_text = """
Commands:
  Natural language: "click on New Note", "double-click the group note"
  Direct: "click 160 677", "double_click 350 187"
  
  screenshot  - Take a screenshot (auto-included with each interaction)
  describe    - Ask GPT-5 to describe what it sees
  undo        - (Not implemented yet)
  help        - Show this help
  quit/exit   - Save session and exit
  
Session is auto-saved to: sessions/session_*.json
"""
            return True, help_text
        
        return None
    
    def run(self):
        """Run the interactive REPL."""
        print("\n" + "="*70)
        print("🏥 Interactive Vista CPRS Assistant with GPT-5")
        print("="*70)
        print("\nType natural language commands like:")
        print('  "click on New Note"')
        print('  "double-click MH RRTP GROUP NOTE"')
        print('  "describe what you see"')
        print("\nOr direct commands: click 160 677, help, quit")
        print(f"\n📁 Session: {self.session.session_file}")
        print("="*70 + "\n")
        
        # Initial screen analysis
        print("📸 Taking initial screenshot and analyzing...")
        try:
            response = self.send_to_gpt5(
                "Please analyze this Vista CPRS screen. Describe the main UI elements you see and their approximate locations.",
                include_screenshot=True
            )
            content, action_data = self.process_response(response)
            if content:
                print(f"\n🤖 GPT-5: {content}\n")
            if action_data:
                success, result = self.execute_action(action_data)
                print(f"   Result: {result}\n")
        except Exception as e:
            print(f"⚠️  Initial analysis failed: {e}\n")
        
        # Main loop
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\n💾 Saving session...")
                    self.session.add_final_summary("User ended session normally")
                    print(f"✅ Session saved to: {self.session.session_file}")
                    break
                
                # Check for direct commands
                direct_result = self.handle_direct_command(user_input)
                if direct_result:
                    success, message = direct_result
                    print(f"   {message}")
                    self.session.log_interaction({
                        "user_input": user_input,
                        "input_type": "direct_command",
                        "action_executed": self.last_action,
                        "action_success": success,
                        "result": message
                    })
                    time.sleep(0.5)  # Brief pause after action
                    continue
                
                # Send to GPT-5
                print("🤔 Analyzing...")
                
                interaction_log = {
                    "user_input": user_input,
                    "input_type": "natural_language"
                }
                
                try:
                    response = self.send_to_gpt5(user_input, include_screenshot=True)
                    content, action_data = self.process_response(response)
                    
                    if content:
                        print(f"\n🤖 GPT-5: {content}")
                    
                    interaction_log["gpt5_response"] = content
                    interaction_log["action_proposed"] = action_data
                    
                    if action_data:
                        action_type = action_data.get("action")
                        reasoning = action_data.get("reasoning", "")
                        
                        if action_type == "describe":
                            # Just a description, no action needed
                            success, result = self.execute_action(action_data)
                            print(f"\n📋 {result}")
                            interaction_log["action_success"] = True
                        else:
                            # Confirm action before executing
                            print(f"\n📍 Proposed: {action_type}")
                            if "x" in action_data and "y" in action_data:
                                print(f"   Coordinates: ({action_data['x']}, {action_data['y']})")
                            if reasoning:
                                print(f"   Reasoning: {reasoning}")
                            
                            confirm = input("   Execute? (y/n/adjust): ").strip().lower()
                            
                            if confirm in ["y", "yes", ""]:
                                success, result = self.execute_action(action_data)
                                status = "✅" if success else "❌"
                                print(f"   {status} {result}")
                                interaction_log["action_executed"] = action_data
                                interaction_log["action_success"] = success
                                interaction_log["result"] = result
                                time.sleep(1)  # Pause to let UI respond
                                
                            elif confirm == "n" or confirm == "no":
                                print("   ⏭️  Skipped")
                                interaction_log["action_executed"] = None
                                interaction_log["user_skipped"] = True
                                
                            else:
                                # User wants to adjust - this is a correction
                                print(f"   📝 Noted. Please provide the correct action.")
                                interaction_log["user_correction"] = confirm
                                interaction_log["action_executed"] = None
                    
                    self.session.log_interaction(interaction_log)
                    
                except requests.exceptions.HTTPError as e:
                    print(f"❌ API Error: {e}")
                    interaction_log["error"] = str(e)
                    self.session.log_interaction(interaction_log)
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    interaction_log["error"] = str(e)
                    self.session.log_interaction(interaction_log)
                
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\n💾 Saving session (interrupted)...")
                self.session.add_final_summary("User interrupted with Ctrl+C")
                print(f"✅ Session saved to: {self.session.session_file}")
                break


def main():
    assistant = InteractiveCPRS()
    assistant.run()


if __name__ == "__main__":
    main()

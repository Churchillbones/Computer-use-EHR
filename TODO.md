# GPT-5 Azure Computer Use Demo - Detailed TODO List

## Phase 0: Prerequisites (Complete Before Phase 1)

### Environment Setup
- [ ] Install Python 3.11+ on Windows
- [ ] Create project virtual environment: `python -m venv venv`
- [ ] Activate virtual environment: `.\venv\Scripts\Activate.ps1`

### Install Dependencies
- [ ] Install OpenAI SDK: `pip install openai`
- [ ] Install Azure Identity: `pip install azure-identity`
- [ ] Install pyautogui: `pip install pyautogui`
- [ ] Install Pillow: `pip install Pillow`
- [ ] Install pytest: `pip install pytest pytest-cov pytest-asyncio`
- [ ] Install python-dotenv: `pip install python-dotenv`
- [ ] Generate requirements.txt: `pip freeze > requirements.txt`

### Configuration
- [ ] Verify `.env` file exists with:
  - [ ] `VA_OPENAI_BASE_URL` (chat completions endpoint)
  - [ ] `VA_OPENAI_RESPONSES_URL` (responses endpoint)
  - [ ] `VA_OPENAI_API_KEY` (primary key)
  - [ ] `VA_OPENAI_API_KEY_2` (secondary key for testing)
  - [ ] `VA_OPENAI_API_VERSION=2025-01-01-preview`
  - [ ] `VA_GPT5_DEPLOYMENT=gpt-5`
  - [ ] `VA_GPT5_MODEL_NAME=gpt-5`
- [ ] Create `.env.example` template (without secrets)
- [ ] Add `.env` to `.gitignore`

### Project Structure
- [ ] Create `src/` directory for source code
- [ ] Create `tests/` directory for pytest tests
- [ ] Create `src/__init__.py`
- [ ] Create `tests/__init__.py`
- [ ] Create `conftest.py` for pytest fixtures

---

## Phase 1: API Endpoint Validation

### Chat Completions Endpoint Tests
- [ ] Create `src/clients/__init__.py`
- [ ] Create `src/clients/chat_client.py` with `ChatCompletionsClient` class
- [ ] Write test: `tests/test_chat_completions.py`
  - [ ] Test API Key 1 authentication
  - [ ] Test API Key 2 authentication
  - [ ] Test simple prompt/response
  - [ ] Test error handling (invalid key, timeout)
- [ ] Run tests and verify all pass

### Responses API Endpoint Tests
- [ ] Create `src/clients/responses_client.py` with `ResponsesAPIClient` class
- [ ] Write test: `tests/test_responses_api.py`
  - [ ] Test API Key 1 authentication
  - [ ] Test API Key 2 authentication
  - [ ] Test basic response creation
  - [ ] Test `previous_response_id` chaining
  - [ ] Test error handling
- [ ] Run tests and verify all pass

### Validation Matrix
| Endpoint | Key 1 | Key 2 |
|----------|-------|-------|
| Chat Completions | [ ] | [ ] |
| Responses API | [ ] | [ ] |

### Phase 1 Exit Criteria
- [ ] All 8 endpoint/key combinations tested
- [ ] Test results documented
- [ ] Any issues logged and resolved

---

## Phase 2: Test Case Infrastructure

### Screen Controller Module
- [ ] Create `src/screen/__init__.py`
- [ ] Create `src/screen/screen_controller.py` with `ScreenController` class
  - [ ] Method: `capture_screenshot() -> PIL.Image`
  - [ ] Method: `screenshot_to_base64() -> str`
  - [ ] Method: `get_screen_size() -> tuple[int, int]`
- [ ] Write test: `tests/test_screen_controller.py`
  - [ ] Test screenshot capture
  - [ ] Test base64 encoding
  - [ ] Test screen dimensions
- [ ] Run tests and verify all pass

### Action Handler Module
- [ ] Create `src/actions/__init__.py`
- [ ] Create `src/actions/action_handler.py` with `ActionHandler` class
  - [ ] Method: `click(x: int, y: int, button: str)`
  - [ ] Method: `double_click(x: int, y: int)`
  - [ ] Method: `type_text(text: str, interval: float)`
  - [ ] Method: `press_key(key: str)`
  - [ ] Method: `hotkey(*keys: str)`
  - [ ] Method: `scroll(x: int, y: int, clicks: int)`
  - [ ] Method: `move_to(x: int, y: int)`
  - [ ] Method: `validate_coordinates(x: int, y: int) -> tuple[int, int]`
- [ ] Write test: `tests/test_action_handler.py`
  - [ ] Test coordinate validation
  - [ ] Test click actions (mock pyautogui)
  - [ ] Test keyboard actions (mock pyautogui)
- [ ] Run tests and verify all pass

### Computer Use Client Module
- [ ] Create `src/clients/computer_use_client.py` with `ComputerUseClient` class
  - [ ] Method: `create_session(task: str, screenshot: str) -> Response`
  - [ ] Method: `send_screenshot(response_id: str, call_id: str, screenshot: str) -> Response`
  - [ ] Method: `extract_computer_calls(response) -> list`
  - [ ] Method: `handle_safety_checks(checks: list) -> list`
- [ ] Write test: `tests/test_computer_use_client.py`
  - [ ] Test session creation
  - [ ] Test response parsing
  - [ ] Test safety check extraction
- [ ] Run tests and verify all pass

### Integration Test
- [ ] Create `tests/test_integration.py`
  - [ ] Test: Capture screenshot → Send to API → Parse response
  - [ ] Test: Execute action from response → Capture new screenshot
- [ ] Run integration tests and verify pass

### Phase 2 Exit Criteria
- [ ] All unit tests pass (>90% coverage)
- [ ] Integration test passes
- [ ] All classes follow OOP principles
- [ ] All methods have docstrings

---

## Phase 3: EHR Progress Note Automation

### EHR Automator Module
- [ ] Create `src/ehr/__init__.py`
- [ ] Create `src/ehr/ehr_automator.py` with `EHRAutomator` class
  - [ ] Property: `workflow_steps: list[str]`
  - [ ] Method: `run_workflow(task: str, max_iterations: int) -> bool`
  - [ ] Method: `process_action(action) -> None`
  - [ ] Method: `wait_for_human_confirmation(check) -> bool`
- [ ] Write test: `tests/test_ehr_automator.py`
  - [ ] Test workflow initialization
  - [ ] Test action processing
  - [ ] Test iteration limits
- [ ] Run tests and verify all pass

### EHR Workflow Definition
- [ ] Document EHR navigation steps in `src/ehr/workflows.py`
  - [ ] Step 1: Open patient chart (placeholder)
  - [ ] Step 2: Navigate to progress notes
  - [ ] Step 3: Create new note
  - [ ] Step 4: Enter note content
  - [ ] Step 5: Save note
  - [ ] Step 6: Verify confirmation
- [ ] Create workflow configuration (JSON or Python dict)

### End-to-End Test
- [ ] Create `tests/test_ehr_e2e.py`
  - [ ] Test: Full progress note workflow with test EHR
  - [ ] Test: Safety check handling
  - [ ] Test: Error recovery
- [ ] Run E2E test with human oversight
- [ ] Document results

### Main Entry Point
- [ ] Create `src/main.py` with CLI interface
  - [ ] Command: `--test-connection` (validate API)
  - [ ] Command: `--run-workflow` (execute EHR automation)
  - [ ] Command: `--dry-run` (simulate without actions)
- [ ] Write test: `tests/test_main.py`
- [ ] Run tests and verify all pass

### Phase 3 Exit Criteria
- [ ] Progress note workflow completes successfully
- [ ] Human oversight maintained throughout
- [ ] All safety checks handled appropriately
- [ ] Results documented with screenshots/logs

---

## Final Checklist

- [ ] All tests passing: `pytest tests/ -v --cov=src`
- [ ] Code coverage > 80%
- [ ] All classes have docstrings
- [ ] README.md created with usage instructions
- [ ] Demo recording captured (optional)
- [ ] Lessons learned documented
- [ ] Code pushed to GitHub: https://github.com/Churchillbones/Computer-use-EHR

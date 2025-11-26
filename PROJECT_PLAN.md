# GPT-5 Azure Computer Use Demo - Project Plan

## Overview

This project tests the Azure OpenAI GPT-5 Computer Use API (preview) for automating EHR progress note creation. The system uses the Responses API with `computer-use-preview` model to control Windows desktop applications via screen capture and simulated mouse/keyboard input.

**Important:** This is a test/simulation environment only and will not affect patient care.

---

## Objective 1: API Endpoint Validation

**Goal:** Verify GPT-5 endpoints work with both Chat Completions and Responses API, and confirm API keys are functional.

### Scope
- Test VA Azure OpenAI Chat Completions endpoint (`/v1/chat/completions/`)
- Test VA Azure OpenAI Responses endpoint (`/v1/responses/`)
- Validate both API keys work with each endpoint
- Confirm `gpt-5` deployment is accessible
- Document response formats and error handling

### Success Criteria
- [ ] Chat Completions endpoint returns valid response with API Key 1
- [ ] Chat Completions endpoint returns valid response with API Key 2
- [ ] Responses API endpoint returns valid response with API Key 1
- [ ] Responses API endpoint returns valid response with API Key 2
- [ ] Error responses are properly captured and logged

---

## Objective 2: Build Test Case Infrastructure

**Goal:** Create a pytest-based testing framework with screen capture and action execution capabilities.

### Scope
- Set up Python virtual environment with required dependencies
- Implement screen capture utilities using pyautogui/PIL
- Create action handler classes for mouse/keyboard control
- Build Computer Use client wrapper for Azure OpenAI Responses API
- Develop pytest fixtures for mocking and integration tests

### Success Criteria
- [ ] All unit tests pass for screen capture utilities
- [ ] All unit tests pass for action handlers (click, type, scroll, screenshot)
- [ ] Integration test successfully sends screenshot to Responses API
- [ ] Test coverage reports generated

---

## Objective 3: EHR Progress Note Automation

**Goal:** Test if the Computer Use model can complete and save a progress note in the EHR application.

### Scope
- Define EHR workflow steps (navigate, open note, write content, save)
- Implement EHR-specific test scenarios
- Handle safety checks and user confirmations
- Create end-to-end test for progress note creation
- Document results and model behavior

### Workflow Steps (Placeholder - Customize for your EHR)
1. Open Patient Chart
2. Navigate to Progress Notes section
3. Click "New Note" or equivalent
4. Enter note content (typed by model)
5. Save/Sign the note
6. Verify save confirmation

### Success Criteria
- [ ] Model can identify EHR UI elements from screenshots
- [ ] Model successfully navigates to progress note section
- [ ] Model can type note content into text fields
- [ ] Model can save the progress note
- [ ] Safety checks are properly handled
- [ ] Human operator maintains oversight throughout

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| API Client | openai SDK |
| Screen Control | pyautogui |
| Image Processing | Pillow (PIL) |
| Testing | pytest |
| Configuration | python-dotenv |
| Environment | Windows |

---

## Safety Considerations

1. **Non-Production Environment:** All testing occurs in simulation/test environment
2. **Human Oversight:** Operator monitors all model actions
3. **Safety Checks:** Model safety checks are acknowledged only after human review
4. **No Patient Data:** Testing uses dummy/test data only
5. **Fail-Safe:** pyautogui fail-safe enabled (move mouse to corner to abort)

---

## Repository

**GitHub:** https://github.com/Churchillbones/Computer-use-EHR

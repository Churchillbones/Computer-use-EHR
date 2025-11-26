# GPT-5 Azure Computer Use Demo

A Python project for testing Azure OpenAI's Computer Use API (preview) to automate EHR progress note creation.

**⚠️ Important:** This is a test/simulation environment only and will not affect patient care.

## Overview

This project demonstrates how to use the Azure OpenAI `computer-use-preview` model to:
- Control Windows desktop applications via screen capture and simulated mouse/keyboard input
- Automate EHR (Electronic Health Record) progress note creation
- Test and validate API connectivity with VA Azure OpenAI endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- Windows OS
- Access to Azure OpenAI `computer-use-preview` model

### Installation

1. Clone the repository:
```powershell
git clone https://github.com/Churchillbones/Computer-use-EHR.git
cd Computer-use-EHR
```

2. Create and activate virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Configure environment:
```powershell
# Copy example env file
copy .env.example .env

# Edit .env with your actual API credentials
```

### Configuration

Edit `.env` with your Azure OpenAI credentials:

```env
VA_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/chat/completions/
VA_OPENAI_RESPONSES_URL=https://your-resource.openai.azure.com/openai/v1/responses/
VA_OPENAI_API_KEY=your-api-key
VA_OPENAI_API_VERSION=2025-01-01-preview
VA_GPT5_DEPLOYMENT=gpt-5
```

### Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_chat_completions.py -v
```

## Project Structure

```
Computer use demo/
├── .env                    # Environment variables (not committed)
├── .env.example            # Template for .env
├── .gitignore
├── requirements.txt
├── PROJECT_PLAN.md         # Project objectives and success criteria
├── TODO.md                 # Detailed task checklist
├── Agent.md                # Instructions for AI coding agents
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py          # Abstract base client
│   │   ├── chat_client.py          # Chat Completions API client
│   │   └── responses_client.py     # Responses API client
│   ├── screen/
│   │   ├── __init__.py
│   │   └── screen_controller.py    # Screen capture utilities
│   └── actions/
│       ├── __init__.py
│       └── action_handler.py       # Mouse/keyboard action handler
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures
    ├── test_chat_completions.py
    ├── test_responses_api.py
    ├── test_screen_controller.py
    └── test_action_handler.py
```

## Documentation

- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Project objectives and success criteria
- [TODO.md](TODO.md) - Detailed task checklist for each phase
- [Agent.md](Agent.md) - Instructions for AI coding assistants (TDD/OOP standards)

## Safety Considerations

1. **Non-Production Environment:** All testing occurs in simulation/test environment
2. **Human Oversight:** Operator monitors all model actions
3. **Safety Checks:** Model safety checks are acknowledged only after human review
4. **No Patient Data:** Testing uses dummy/test data only
5. **Fail-Safe:** pyautogui fail-safe enabled (move mouse to corner to abort)

## License

Internal VA project - not for public distribution.

## Resources

- [Azure OpenAI Computer Use Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/computer-use)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [pyautogui Documentation](https://pyautogui.readthedocs.io/)

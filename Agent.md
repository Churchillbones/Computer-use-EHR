# Agent Instructions - GPT-5 Azure Computer Use Demo

## Purpose

This file provides guidance for LLMs and AI coding agents working on this project. Follow these instructions to maintain code quality, consistency, and alignment with project goals.

---

## Development Methodology

### Test-Driven Development (TDD)

**All code changes MUST follow the Red-Green-Refactor cycle:**

1. **RED:** Write a failing test first
   - Define expected behavior before implementation
   - Test should fail because the feature doesn't exist yet
   - Commit the failing test

2. **GREEN:** Write minimal code to pass the test
   - Implement only what's needed to make the test pass
   - Don't over-engineer or add extra features
   - Commit when tests pass

3. **REFACTOR:** Improve code quality
   - Clean up implementation while keeping tests green
   - Remove duplication, improve naming, simplify logic
   - Commit after refactoring

### TDD Example Workflow

```python
# Step 1: RED - Write failing test first
def test_screenshot_to_base64_returns_string():
    controller = ScreenController()
    result = controller.screenshot_to_base64()
    assert isinstance(result, str)
    assert len(result) > 0

# Step 2: GREEN - Implement minimal code
class ScreenController:
    def screenshot_to_base64(self) -> str:
        screenshot = pyautogui.screenshot()
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Step 3: REFACTOR - Improve if needed
```

---

## Object-Oriented Programming (OOP) Standards

### Class Design Principles

1. **Single Responsibility Principle (SRP)**
   - Each class should have one reason to change
   - Example: `ScreenController` handles screen capture only, not actions

2. **Open/Closed Principle (OCP)**
   - Classes should be open for extension, closed for modification
   - Use inheritance and composition to extend behavior

3. **Dependency Injection**
   - Pass dependencies into constructors, don't hard-code them
   - Makes testing easier with mocks

4. **Encapsulation**
   - Use private attributes (prefix with `_`) for internal state
   - Expose behavior through public methods

### Required Class Structure

```python
"""Module docstring explaining purpose."""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ClassName:
    """
    Class docstring with description.
    
    Attributes:
        attribute_name: Description of attribute.
    
    Example:
        >>> obj = ClassName(param="value")
        >>> obj.method()
    """
    
    def __init__(self, dependency: DependencyType) -> None:
        """
        Initialize ClassName.
        
        Args:
            dependency: Description of dependency.
        """
        self._dependency = dependency
        self._internal_state: Optional[str] = None
    
    def public_method(self, param: str) -> ReturnType:
        """
        Method docstring with description.
        
        Args:
            param: Description of parameter.
        
        Returns:
            Description of return value.
        
        Raises:
            ValueError: When param is invalid.
        """
        logger.info(f"Executing public_method with {param}")
        return self._private_helper(param)
    
    def _private_helper(self, param: str) -> ReturnType:
        """Private method for internal use."""
        pass
```

---

## Project Architecture

### Directory Structure

```
Computer use demo/
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example            # Template for .env
├── .gitignore
├── requirements.txt
├── conftest.py             # Pytest fixtures
├── PROJECT_PLAN.md
├── TODO.md
├── Agent.md
├── src/
│   ├── __init__.py
│   ├── main.py             # CLI entry point
│   ├── config.py           # Configuration management
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py          # BaseClient ABC
│   │   ├── chat_client.py          # ChatCompletionsClient
│   │   ├── responses_client.py     # ResponsesAPIClient
│   │   └── computer_use_client.py  # ComputerUseClient
│   ├── screen/
│   │   ├── __init__.py
│   │   └── screen_controller.py    # ScreenController
│   ├── actions/
│   │   ├── __init__.py
│   │   └── action_handler.py       # ActionHandler
│   └── ehr/
│       ├── __init__.py
│       ├── ehr_automator.py        # EHRAutomator
│       └── workflows.py            # Workflow definitions
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures
    ├── test_chat_completions.py
    ├── test_responses_api.py
    ├── test_screen_controller.py
    ├── test_action_handler.py
    ├── test_computer_use_client.py
    ├── test_ehr_automator.py
    ├── test_integration.py
    └── test_ehr_e2e.py
```

### Class Hierarchy

```
BaseClient (ABC)
├── ChatCompletionsClient
├── ResponsesAPIClient
└── ComputerUseClient

ScreenController (standalone)

ActionHandler (standalone)

EHRAutomator
└── uses: ComputerUseClient, ScreenController, ActionHandler
```

---

## Pytest Guidelines

### Fixture Usage

```python
# conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_openai_client():
    """Provide a mocked OpenAI client."""
    with patch('src.clients.computer_use_client.OpenAI') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def screen_controller():
    """Provide a ScreenController instance."""
    return ScreenController()

@pytest.fixture
def sample_screenshot_base64():
    """Provide a sample base64 screenshot for testing."""
    # Small 1x1 white PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
```

### Test Naming Convention

```python
def test_<method_name>_<scenario>_<expected_result>():
    """Test that <method> does <expected> when <scenario>."""
    pass

# Examples:
def test_click_with_valid_coordinates_executes_successfully():
def test_click_with_negative_coordinates_raises_value_error():
def test_screenshot_to_base64_returns_non_empty_string():
```

### Mocking External Dependencies

```python
def test_capture_screenshot_calls_pyautogui(mocker):
    """Test that capture_screenshot uses pyautogui."""
    mock_screenshot = mocker.patch('pyautogui.screenshot')
    mock_screenshot.return_value = Mock()
    
    controller = ScreenController()
    controller.capture_screenshot()
    
    mock_screenshot.assert_called_once()
```

---

## Configuration Management

### Environment Variables

Always load configuration from `.env`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration from environment."""
    
    # API Endpoints
    OPENAI_BASE_URL: str = os.getenv("VA_OPENAI_BASE_URL", "")
    OPENAI_RESPONSES_URL: str = os.getenv("VA_OPENAI_RESPONSES_URL", "")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("VA_OPENAI_API_KEY", "")
    OPENAI_API_KEY_2: str = os.getenv("VA_OPENAI_API_KEY_2", "")
    
    # Model Configuration
    OPENAI_API_VERSION: str = os.getenv("VA_OPENAI_API_VERSION", "2025-01-01-preview")
    GPT5_DEPLOYMENT: str = os.getenv("VA_GPT5_DEPLOYMENT", "gpt-5")
    GPT5_MODEL_NAME: str = os.getenv("VA_GPT5_MODEL_NAME", "gpt-5")
    
    # Display Settings
    DISPLAY_WIDTH: int = int(os.getenv("DISPLAY_WIDTH", "1920"))
    DISPLAY_HEIGHT: int = int(os.getenv("DISPLAY_HEIGHT", "1080"))
    
    # Automation Settings
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
```

---

## Error Handling

### Standard Pattern

```python
import logging
from typing import Optional, Callable, Any
import time

logger = logging.getLogger(__name__)


class ComputerUseError(Exception):
    """Base exception for computer use errors."""
    pass


class APIConnectionError(ComputerUseError):
    """Raised when API connection fails."""
    pass


class ActionExecutionError(ComputerUseError):
    """Raised when action execution fails."""
    pass


class SafetyCheckError(ComputerUseError):
    """Raised when safety check is not acknowledged."""
    pass


def execute_with_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0
) -> Optional[Any]:
    """Execute function with retry logic."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    raise ComputerUseError(f"Failed after {max_retries} attempts")
```

---

## Code Review Checklist

Before committing any code, verify:

- [ ] Tests written BEFORE implementation (TDD)
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code coverage maintained: `pytest --cov=src --cov-report=term-missing`
- [ ] Type hints on all function signatures
- [ ] Docstrings on all public classes and methods
- [ ] No hardcoded secrets or API keys
- [ ] Logging added for key operations
- [ ] Error handling with specific exceptions
- [ ] Private methods prefixed with `_`

---

## Prohibited Practices

❌ **DO NOT:**
- Commit `.env` or any file containing API keys
- Skip writing tests before implementation
- Use `print()` instead of `logging`
- Hardcode configuration values
- Catch bare `except:` without specific exception types
- Create god classes with multiple responsibilities
- Ignore type hints
- Write tests after implementation is complete

---

## Quick Reference Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_screen_controller.py -v

# Run tests matching pattern
pytest -k "test_click" -v

# Install dependencies
pip install -r requirements.txt

# Generate requirements.txt
pip freeze > requirements.txt

# Git commands
git add .
git commit -m "Description of changes"
git push origin main
```

---

## Repository

**GitHub:** https://github.com/Churchillbones/Computer-use-EHR

---

## Contact & Resources

- **Azure OpenAI Computer Use Docs:** https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/computer-use
- **OpenAI Python SDK:** https://github.com/openai/openai-python
- **pyautogui Docs:** https://pyautogui.readthedocs.io/
- **pytest Docs:** https://docs.pytest.org/

"""
Phase 1: API Endpoint Validation Script

This script tests both Chat Completions and Responses API endpoints
with both API keys to verify connectivity.

Usage:
    python -m src.validate_endpoints
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.chat_client import ChatCompletionsClient
from src.clients.responses_client import ResponsesAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_chat_completions(base_url: str, api_key: str, key_name: str, model: str) -> bool:
    """
    Test Chat Completions endpoint with given API key.
    
    Args:
        base_url: The chat completions endpoint URL.
        api_key: The API key to test.
        key_name: Name identifier for the key (for logging).
        model: The model/deployment name.
    
    Returns:
        True if test passes, False otherwise.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Chat Completions with {key_name}")
    logger.info(f"URL: {base_url}")
    logger.info(f"Model: {model}")
    logger.info('='*60)
    
    try:
        client = ChatCompletionsClient(
            base_url=base_url,
            api_key=api_key,
            model=model
        )
        
        response = client.send_message(
            message="Hello, please respond with 'Connection successful' if you can read this.",
            max_tokens=50
        )
        
        if response:
            text = client.get_completion_text(response)
            logger.info(f"✅ SUCCESS - Response received")
            logger.info(f"   Response: {text[:100] if text else 'No text'}...")
            logger.info(f"   Model: {response.get('model', 'N/A')}")
            logger.info(f"   Usage: {response.get('usage', {})}")
            return True
        else:
            logger.error(f"❌ FAILED - No response received")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED - {type(e).__name__}: {e}")
        return False


def test_responses_api(base_url: str, api_key: str, key_name: str, model: str) -> bool:
    """
    Test Responses API endpoint with given API key.
    
    Args:
        base_url: The responses endpoint URL.
        api_key: The API key to test.
        key_name: Name identifier for the key (for logging).
        model: The model/deployment name.
    
    Returns:
        True if test passes, False otherwise.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Responses API with {key_name}")
    logger.info(f"URL: {base_url}")
    logger.info(f"Model: {model}")
    logger.info('='*60)
    
    try:
        client = ResponsesAPIClient(
            base_url=base_url,
            api_key=api_key,
            model=model
        )
        
        # Test without computer tool first (simpler test)
        response = client.create_response(
            task="Hello, please respond with 'Connection successful' if you can read this.",
            include_computer_tool=False
        )
        
        if response:
            text = client.extract_text_output(response)
            logger.info(f"✅ SUCCESS - Response received")
            logger.info(f"   Response ID: {response.get('id', 'N/A')}")
            logger.info(f"   Text: {text[:100] if text else 'No text output'}...")
            return True
        else:
            logger.error(f"❌ FAILED - No response received")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED - {type(e).__name__}: {e}")
        return False


def test_computer_use(base_url: str, api_key: str, key_name: str, model: str) -> bool:
    """
    Test Computer Use functionality with Responses API.
    
    Args:
        base_url: The responses endpoint URL.
        api_key: The API key to test.
        key_name: Name identifier for the key (for logging).
        model: The model/deployment name for computer use.
    
    Returns:
        True if test passes, False otherwise.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Computer Use with {key_name}")
    logger.info(f"URL: {base_url}")
    logger.info(f"Model: {model}")
    logger.info('='*60)
    
    try:
        client = ResponsesAPIClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            display_width=1920,
            display_height=1080
        )
        
        # Test with computer tool
        response = client.create_response(
            task="Take a screenshot to see the current screen state.",
            include_computer_tool=True,
            environment="windows"
        )
        
        if response:
            computer_calls = client.extract_computer_calls(response)
            logger.info(f"✅ SUCCESS - Response received")
            logger.info(f"   Response ID: {response.get('id', 'N/A')}")
            logger.info(f"   Computer calls: {len(computer_calls)}")
            
            if computer_calls:
                for i, call in enumerate(computer_calls):
                    action = call.get('action', {})
                    logger.info(f"   Call {i+1}: {action.get('type', 'unknown')}")
            
            return True
        else:
            logger.error(f"❌ FAILED - No response received")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED - {type(e).__name__}: {e}")
        return False


def main():
    """Run all endpoint validation tests."""
    
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: API ENDPOINT VALIDATION")
    logger.info("="*60)
    
    # Get configuration from environment
    chat_url = os.getenv("VA_OPENAI_BASE_URL", "")
    responses_url = os.getenv("VA_OPENAI_RESPONSES_URL", "")
    api_key_1 = os.getenv("VA_OPENAI_API_KEY", "")
    api_key_2 = os.getenv("VA_OPENAI_API_KEY_2", "")
    gpt5_model = os.getenv("VA_GPT5_DEPLOYMENT", "gpt-5")
    computer_use_model = os.getenv("VA_COMPUTER_USE_DEPLOYMENT", "computer-use-preview")
    
    # Validation
    missing = []
    if not chat_url:
        missing.append("VA_OPENAI_BASE_URL")
    if not api_key_1:
        missing.append("VA_OPENAI_API_KEY")
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please check your .env file")
        return False
    
    # If responses URL not set, derive from chat URL
    if not responses_url:
        # Try to derive responses URL from chat URL
        if "/chat/completions" in chat_url:
            responses_url = chat_url.replace("/chat/completions", "/responses")
            logger.info(f"Derived responses URL: {responses_url}")
        else:
            logger.warning("VA_OPENAI_RESPONSES_URL not set and could not derive from chat URL")
    
    # Results tracking
    results = {
        "Chat Completions - Key 1": None,
        "Chat Completions - Key 2": None,
        "Responses API - Key 1": None,
        "Responses API - Key 2": None,
        "Computer Use - Key 1": None,
        "Computer Use - Key 2": None,
    }
    
    # Test Chat Completions with Key 1
    results["Chat Completions - Key 1"] = test_chat_completions(
        chat_url, api_key_1, "API Key 1", gpt5_model
    )
    
    # Test Chat Completions with Key 2 (if available)
    if api_key_2:
        results["Chat Completions - Key 2"] = test_chat_completions(
            chat_url, api_key_2, "API Key 2", gpt5_model
        )
    else:
        logger.warning("VA_OPENAI_API_KEY_2 not set - skipping Key 2 tests")
        results["Chat Completions - Key 2"] = "SKIPPED"
    
    # Test Responses API with Key 1 (if URL available)
    if responses_url:
        results["Responses API - Key 1"] = test_responses_api(
            responses_url, api_key_1, "API Key 1", gpt5_model
        )
        
        # Test Responses API with Key 2 (if available)
        if api_key_2:
            results["Responses API - Key 2"] = test_responses_api(
                responses_url, api_key_2, "API Key 2", gpt5_model
            )
        else:
            results["Responses API - Key 2"] = "SKIPPED"
        
        # Test Computer Use with Key 1
        results["Computer Use - Key 1"] = test_computer_use(
            responses_url, api_key_1, "API Key 1", computer_use_model
        )
        
        # Test Computer Use with Key 2 (if available)
        if api_key_2:
            results["Computer Use - Key 2"] = test_computer_use(
                responses_url, api_key_2, "API Key 2", computer_use_model
            )
        else:
            results["Computer Use - Key 2"] = "SKIPPED"
    else:
        logger.warning("Responses URL not available - skipping Responses API and Computer Use tests")
        results["Responses API - Key 1"] = "SKIPPED"
        results["Responses API - Key 2"] = "SKIPPED"
        results["Computer Use - Key 1"] = "SKIPPED"
        results["Computer Use - Key 2"] = "SKIPPED"
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        logger.info(f"  {test_name}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r not in [True, False])
    
    logger.info(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

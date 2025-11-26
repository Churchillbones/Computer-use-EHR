"""
Phase 1: Quick API Endpoint Test Script

Tests specific endpoints to determine correct URL structure.

Usage:
    python -m src.test_endpoints_quick
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def test_endpoint(url: str, api_key: str, payload: dict, description: str) -> dict:
    """Test a specific endpoint and return results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {description}")
    logger.info(f"URL: {url}")
    logger.info('='*60)
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"✅ SUCCESS")
            result = response.json()
            logger.info(f"Response keys: {list(result.keys())}")
            return {"success": True, "status": response.status_code, "data": result}
        else:
            logger.error(f"❌ FAILED - Status {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return {"success": False, "status": response.status_code, "error": response.text}
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ TIMEOUT")
        return {"success": False, "error": "Timeout"}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ CONNECTION ERROR: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"❌ ERROR: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e)}


def main():
    # Get API key from environment
    api_key = os.getenv("VA_OPENAI_API_KEY", "")
    model = os.getenv("VA_GPT5_DEPLOYMENT", "gpt-5")
    
    if not api_key:
        logger.error("VA_OPENAI_API_KEY not set in .env file")
        return
    
    logger.info(f"Using model/deployment: {model}")
    logger.info(f"API Key (first 10 chars): {api_key[:10]}...")
    
    # Base URLs to test
    base_urls = [
        "https://spd-dev-openai-std-apim.azure-api.us/openai/v1",
        "https://spd-prod-openai-va-apim.azure-api.us",
    ]
    
    # Chat completions payload
    chat_payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say hello in one word."}
        ],
        "max_tokens": 10
    }
    
    # Responses API payload (simple, no computer tool)
    responses_payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "Say hello in one word."}]
            }
        ],
        "truncation": "auto"
    }
    
    results = []
    
    for base_url in base_urls:
        logger.info(f"\n\n{'#'*60}")
        logger.info(f"TESTING BASE URL: {base_url}")
        logger.info(f"{'#'*60}")
        
        # Test various endpoint patterns
        endpoints_to_test = [
            # Chat completions variations
            (f"{base_url}/chat/completions", chat_payload, "Chat Completions (v1/chat/completions)"),
            (f"{base_url}/chat/completions/", chat_payload, "Chat Completions (with trailing slash)"),
            
            # Responses API variations
            (f"{base_url}/responses", responses_payload, "Responses API (v1/responses)"),
            (f"{base_url}/responses/", responses_payload, "Responses API (with trailing slash)"),
            
            # OpenAI-style paths
            (f"{base_url}/openai/deployments/{model}/chat/completions", chat_payload, f"Deployments Chat ({model})"),
        ]
        
        # If base URL doesn't have /v1, also test with /openai/v1 prefix
        if "/v1" not in base_url:
            endpoints_to_test.extend([
                (f"{base_url}/openai/v1/chat/completions", chat_payload, "OpenAI v1 Chat Completions"),
                (f"{base_url}/openai/v1/responses", responses_payload, "OpenAI v1 Responses"),
            ])
        
        for url, payload, description in endpoints_to_test:
            result = test_endpoint(url, api_key, payload, description)
            results.append({
                "base_url": base_url,
                "endpoint": url,
                "description": description,
                **result
            })
    
    # Summary
    logger.info(f"\n\n{'='*60}")
    logger.info("SUMMARY OF ALL TESTS")
    logger.info('='*60)
    
    for r in results:
        status = "✅" if r.get("success") else "❌"
        logger.info(f"{status} [{r.get('status', 'N/A')}] {r['description']}")
        logger.info(f"   URL: {r['endpoint']}")
    
    # Show working endpoints
    working = [r for r in results if r.get("success")]
    if working:
        logger.info(f"\n\n🎉 WORKING ENDPOINTS:")
        for r in working:
            logger.info(f"   {r['endpoint']}")
    else:
        logger.info(f"\n\n⚠️ No working endpoints found. Check API key and network access.")


if __name__ == "__main__":
    main()

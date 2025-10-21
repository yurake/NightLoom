#!/usr/bin/env python3
"""Test OpenAI configuration and API connectivity."""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from the correct path
load_dotenv(dotenv_path=".env")  # Current directory (backend/)
load_dotenv(dotenv_path="../.env")  # Parent directory (project root)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_openai_config():
    """Test OpenAI configuration and basic connectivity."""
    
    # Check environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    print("=== Environment Variables ===")
    print(f"OPENAI_API_KEY: {'Set' if openai_api_key else 'NOT SET'}")
    if openai_api_key:
        print(f"OPENAI_API_KEY (first 10 chars): {openai_api_key[:10]}...")
    print(f"OPENAI_MODEL: {openai_model}")
    print(f"LOG_LEVEL: {log_level}")
    print()
    
    if not openai_api_key:
        print("❌ OPENAI_API_KEY is not set! This is likely the root cause.")
        return False
    
    # Test OpenAI SDK import
    try:
        from openai import AsyncOpenAI
        print("✅ OpenAI SDK imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI SDK import failed: {e}")
        return False
    
    # Test OpenAI client initialization
    try:
        client = AsyncOpenAI(api_key=openai_api_key)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"❌ OpenAI client initialization failed: {e}")
        return False
    
    # Test basic API connectivity
    try:
        print("🔄 Testing OpenAI API connectivity...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for test
            messages=[{"role": "user", "content": "Hello, respond with just 'Hi'"}],
            max_tokens=10,
            timeout=10
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✅ OpenAI API test successful. Response: '{content}'")
            return True
        else:
            print("❌ OpenAI API test failed: Empty response")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_config())
    exit(0 if success else 1)

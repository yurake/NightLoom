#!/usr/bin/env python3
"""
Simple test script to verify logging functionality.
"""

import logging
import pytest

def test_basic_logging():
    """Test basic logging functionality"""
    logger = logging.getLogger(__name__)
    
    print("=== Testing basic logging ===")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test OpenAI client logging
    openai_logger = logging.getLogger('app.clients.openai_client')
    openai_logger.info("[OpenAI] Test OpenAI client log message")
    
    # Test LLM service logging
    llm_logger = logging.getLogger('app.services.external_llm')
    llm_logger.info("[LLM Service] Test LLM service log message")
    
    # Test template logging
    template_logger = logging.getLogger('app.services.prompt_template')
    template_logger.debug("[PromptTemplate] Test template log message")
    
    # Test API logging
    api_logger = logging.getLogger('app.api.bootstrap')
    api_logger.info("[API] Test API log message")
    
    print("=== Logging test completed ===")

# Remove main execution block as this is now a pytest test

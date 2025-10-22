#!/usr/bin/env python3
"""
Test script to verify logging functionality for OpenAI integration.
"""

import pytest
import logging
import os
from app.main import setup_logging
from app.services.external_llm import get_llm_service
from app.models.session import Session
from app.models.llm_config import get_llm_config

@pytest.mark.asyncio
async def test_logging():
    """Test logging functionality"""
    # Setup logging
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=== Starting logging test ===")
    
    try:
        # Create a test session
        session = Session()
        session.initialCharacter = "あ"
        
        # Get LLM service
        llm_service = get_llm_service()
        
        logger.info(f"Testing keyword generation for character: {session.initialCharacter}")
        
        # Generate keywords (this should trigger fallback and log output)
        keywords = await llm_service.generate_keywords(session)
        
        logger.info(f"Generated keywords: {keywords}")
        logger.info(f"Fallback flags: {session.fallbackFlags}")
        
        print("=== Test completed successfully ===")
        print(f"Keywords generated: {keywords}")
        print(f"Fallback used: {'keyword_generation' in session.fallbackFlags}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"Test failed: {e}")

# Remove main execution block as this is now a pytest test

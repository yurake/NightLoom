#!/usr/bin/env python3
"""
ログレベル設定のテストスクリプト

使用例:
  # デフォルト設定
  uv run python test_logging_configuration.py
  
  # 環境変数指定
  LOG_LEVEL=DEBUG uv run python test_logging_configuration.py
  
  # 個別モジュール指定
  LOG_LEVEL=INFO OPENAI_LOG_LEVEL=DEBUG uv run python test_logging_configuration.py
"""

import os
import sys
import logging

# アプリケーションのログ設定を使用
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import setup_logging

def test_logging_levels():
    """各モジュールのログレベルをテスト"""
    
    # ログ設定
    setup_logging()
    
    # 各レベルのログを出力してテスト
    loggers = {
        'main': logging.getLogger(__name__),
        'openai_client': logging.getLogger('app.clients.openai_client'),
        'llm_service': logging.getLogger('app.services.external_llm'),
        'prompt_template': logging.getLogger('app.services.prompt_template'),
    }
    
    print("=== ログレベル設定テスト ===")
    
    for name, logger in loggers.items():
        print(f"\n{name} logger (level: {logger.level}, effective level: {logger.getEffectiveLevel()}):")
        logger.debug(f"DEBUG message from {name}")
        logger.info(f"INFO message from {name}")
        logger.warning(f"WARNING message from {name}")
        logger.error(f"ERROR message from {name}")
        logger.critical(f"CRITICAL message from {name}")
    
    print("\n=== 環境変数設定 ===")
    print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'default(INFO)')}")
    print(f"OPENAI_LOG_LEVEL: {os.getenv('OPENAI_LOG_LEVEL', 'default(INFO)')}")
    print(f"LLM_SERVICE_LOG_LEVEL: {os.getenv('LLM_SERVICE_LOG_LEVEL', 'default(INFO)')}")
    print(f"PROMPT_LOG_LEVEL: {os.getenv('PROMPT_LOG_LEVEL', 'default(INFO)')}")

if __name__ == "__main__":
    test_logging_levels()

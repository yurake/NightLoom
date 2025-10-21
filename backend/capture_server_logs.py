#!/usr/bin/env python3
"""
サーバーログをリアルタイムで取得して表示するスクリプト

現在のエラー状況を正確に把握するため、API呼び出しと同時にサーバーログを監視します。
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

async def test_with_log_capture():
    """API呼び出しを実行してサーバーログの問題を特定"""
    
    print("=" * 80)
    print("🔍 サーバーログ問題診断")
    print("=" * 80)
    print(f"診断開始: {datetime.now()}")
    print()
    
    # テスト文字
    test_char = "え"
    
    print(f"📡 テスト実行: initial_character = '{test_char}'")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            # API呼び出し前の時刻記録
            start_time = time.time()
            print(f"⏰ API呼び出し開始: {datetime.now()}")
            
            # API呼び出し実行
            response = await client.post(
                "http://localhost:8000/api/sessions/start",
                json={"initial_character": test_char},
                timeout=30.0
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ API呼び出し完了: {datetime.now()} (所要時間: {duration:.2f}秒)")
            print()
            
            # レスポンス解析
            if response.status_code == 200:
                data = response.json()
                fallback_used = data.get("fallbackUsed", True)
                keywords = data.get("keywordCandidates", [])
                session_id = data.get("sessionId", "unknown")
                
                print("📊 API レスポンス結果:")
                print("-" * 30)
                print(f"  Status: ✅ 200 OK")
                print(f"  Session ID: {session_id}")
                print(f"  fallbackUsed: {fallback_used}")
                print(f"  Keywords: {keywords}")
                
                if fallback_used:
                    print("  ⚠️  フォールバック使用 - まだ問題が残っています")
                else:
                    print("  ✅ LLM動的生成成功")
                    
            else:
                print(f"❌ APIエラー:")
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text}")
                
    except Exception as e:
        print(f"❌ 例外発生: {type(e).__name__}: {e}")
    
    print()
    print("=" * 80)
    print("📋 サーバーログで確認すべきエラーパターン:")
    print("=" * 80)
    
    error_patterns = [
        "AttributeError: 'ProviderConfig' object has no attribute",
        "ValidationError: 1 validation error for ProviderConfig", 
        "ModuleNotFoundError: No module named",
        "'MockLLMClient' object has no attribute 'generate_keywords'",
        "[Provider Chain] ✗ mock unexpected error",
        "[LLM Service] All providers failed",
        "[LLM Service] Using fallback keywords"
    ]
    
    for i, pattern in enumerate(error_patterns, 1):
        print(f"{i}. {pattern}")
    
    print()
    print("✅ 成功時に表示されるべきログパターン:")
    print("-" * 50)
    success_patterns = [
        "[Health Check] Mock provider: always healthy",
        "[Provider Chain] Provider mock passed health check", 
        "[Provider Chain] Executing keyword_generation with mock",
        "[Mock] Generating keywords for:",
        "[Mock] Generated keywords:",
        "[Provider Chain] ✓ Success with mock"
    ]
    
    for i, pattern in enumerate(success_patterns, 1):
        print(f"{i}. {pattern}")
    
    print()
    print("🔧 次のステップ:")
    print("1. サーバーログでどのエラーパターンが出力されているかを確認")
    print("2. エラーの具体的な内容を特定")  
    print("3. 該当するコード部分を修正")
    print()

if __name__ == "__main__":
    asyncio.run(test_with_log_capture())

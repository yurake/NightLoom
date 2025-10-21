#!/usr/bin/env python3
"""
LLMヘルスチェック機能のテストスクリプト

サーバーログを詳細に出力して、fallbackUsed問題の解決状況を確認します。
"""

import asyncio
import json
import httpx
from datetime import datetime

async def test_keyword_generation():
    """キーワード生成APIのテストとログ確認"""
    
    print("=" * 60)
    print("LLM Health Check Test")
    print("=" * 60)
    print(f"テスト開始時刻: {datetime.now()}")
    print()
    
    # テスト文字のリスト
    test_characters = ["あ", "か", "さ", "た", "な"]
    
    async with httpx.AsyncClient() as client:
        for i, char in enumerate(test_characters, 1):
            print(f"[テスト {i}] 文字: '{char}'")
            
            try:
                # API呼び出し
                response = await client.post(
                    "http://localhost:8000/api/sessions/start",
                    json={"initial_character": char},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    fallback_used = data.get("fallbackUsed", True)
                    keywords = data.get("keywordCandidates", [])
                    
                    # 結果表示
                    status = "✅ 成功" if not fallback_used else "⚠️  フォールバック"
                    print(f"  結果: {status}")
                    print(f"  fallbackUsed: {fallback_used}")
                    print(f"  keywords: {keywords}")
                    
                    if not fallback_used:
                        print("  → LLMによる動的生成が成功!")
                    else:
                        print("  → フォールバック資産を使用")
                        
                else:
                    print(f"  ❌ エラー: HTTP {response.status_code}")
                    print(f"  レスポンス: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ 例外: {type(e).__name__}: {e}")
            
            print("-" * 40)
            
            # 少し待機（ログ出力の整理のため）
            await asyncio.sleep(0.5)
    
    print()
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)
    print()
    print("📋 確認ポイント:")
    print("1. サーバーログで [Provider Chain] Starting with 3 providers が表示される")
    print("2. Mock provider が ✓ Success with mock で成功している")
    print("3. fallbackUsed: False が表示される")
    print("4. LLMによる動的なキーワード生成が実行される")

if __name__ == "__main__":
    asyncio.run(test_keyword_generation())

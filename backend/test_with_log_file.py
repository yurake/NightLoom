#!/usr/bin/env python3
"""
ログファイル出力を使用してサーバーログを確認するテストスクリプト

サーバー再起動後にAPI呼び出しを行い、ログファイルから詳細な動作状況を確認します。
"""

import subprocess
import json
import time
import os
from datetime import datetime

def clear_log_file():
    """ログファイルをクリア"""
    log_file = "logs/nightloom.log"
    try:
        if os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("")
            print(f"✅ ログファイルをクリア: {log_file}")
        else:
            print(f"📝 新しいログファイルを作成: {log_file}")
    except Exception as e:
        print(f"❌ ログファイルクリアエラー: {e}")

def test_api_call():
    """API呼び出しを実行"""
    print("🚀 API呼び出し実行中...")
    
    cmd = [
        'curl', '-X', 'POST', 'http://localhost:8000/api/sessions/start',
        '-H', 'Content-Type: application/json',
        '-d', '{"initial_character": "け"}',
        '-s'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                fallback_used = data.get('fallbackUsed', True)
                keywords = data.get('keywordCandidates', [])
                
                print("📊 API呼び出し結果:")
                print(f"  fallbackUsed: {fallback_used}")
                print(f"  keywords: {keywords}")
                
                return fallback_used
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")
                return None
        else:
            print(f"❌ API呼び出しエラー: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ API呼び出し例外: {e}")
        return None

def read_log_file():
    """ログファイルの内容を読み取り"""
    log_file = "logs/nightloom.log"
    
    print(f"\n📋 ログファイル内容確認: {log_file}")
    print("=" * 80)
    
    try:
        if not os.path.exists(log_file):
            print("❌ ログファイルが存在しません")
            return
            
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("⚠️  ログファイルが空です")
            return
            
        print(f"📄 ログ行数: {len(lines)}")
        print("-" * 80)
        
        # 最後の50行を表示
        recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        for i, line in enumerate(recent_lines, 1):
            line = line.strip()
            if line:
                # 重要なログパターンをハイライト
                if any(keyword in line for keyword in ['ERROR', 'WARN', 'Provider Chain', 'Health Check', 'Mock']):
                    prefix = "🔍 "
                else:
                    prefix = "   "
                print(f"{prefix}{line}")
        
        print("-" * 80)
        
        # エラーパターンの分析
        analyze_log_patterns(lines)
        
    except Exception as e:
        print(f"❌ ログファイル読み取りエラー: {e}")

def analyze_log_patterns(lines):
    """ログからエラーパターンを分析"""
    print("\n🔍 ログ分析:")
    
    error_patterns = {
        "AttributeError": "設定オブジェクトの属性エラー",
        "ValidationError": "Pydantic検証エラー", 
        "ModuleNotFoundError": "モジュール未発見エラー",
        "Provider Chain": "プロバイダーチェーンの動作",
        "Health Check": "ヘルスチェックの状況",
        "Mock": "Mockプロバイダーの動作",
        "fallback": "フォールバック使用"
    }
    
    found_patterns = {}
    
    for line in lines:
        for pattern, description in error_patterns.items():
            if pattern in line:
                if pattern not in found_patterns:
                    found_patterns[pattern] = []
                found_patterns[pattern].append(line.strip())
    
    if found_patterns:
        for pattern, occurrences in found_patterns.items():
            print(f"\n📌 {pattern} ({error_patterns[pattern]}):")
            for occurrence in occurrences[-3:]:  # 最新3件を表示
                print(f"  • {occurrence}")
    else:
        print("✅ 特別なパターンは検出されませんでした")

def main():
    print("🔧 NightLoom ログファイル確認テスト")
    print("=" * 80)
    print(f"テスト開始: {datetime.now()}")
    print()
    
    # 1. ログファイルをクリア
    clear_log_file()
    
    print("\n⏳ サーバーが再起動されるまで少し待機...")
    time.sleep(3)
    
    # 2. API呼び出し実行
    fallback_used = test_api_call()
    
    # 3. ログファイル確認
    print("\n⏳ ログ出力を待機...")
    time.sleep(2)  # ログ出力のための待機
    
    read_log_file()
    
    # 4. 結果サマリー
    print("\n" + "=" * 80)
    print("📊 テスト結果サマリー")
    print("=" * 80)
    
    if fallback_used is not None:
        if fallback_used:
            print("⚠️  fallbackUsed: true - まだ問題が残っています")
            print("   ログファイルでエラーの詳細を確認してください")
        else:
            print("✅ fallbackUsed: false - 修正が成功しています！")
            print("   LLMによる動的生成が正常に動作中")
    else:
        print("❌ API呼び出しに失敗しました")
    
    print(f"\n📋 ログファイル: backend/logs/nightloom.log")
    print("   継続的な監視には: tail -f backend/logs/nightloom.log")

if __name__ == "__main__":
    main()

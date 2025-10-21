#!/usr/bin/env python3
"""
サーバーの再起動を待機してからテストを実行するスクリプト

サーバーが利用可能になるまで待機し、その後API呼び出しとログ確認を行います。
"""

import subprocess
import json
import time
import os
from datetime import datetime

def wait_for_server(max_wait=60):
    """サーバーが起動するまで待機"""
    print("⏳ サーバーの起動を待機中...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            result = subprocess.run(['curl', '-s', 'http://localhost:8000/health'], 
                                   capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("✅ サーバーが起動しました！")
                return True
                
        except Exception:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\n❌ サーバーが{max_wait}秒以内に起動しませんでした")
    return False

def test_api_and_check_logs():
    """API呼び出しとログファイル確認"""
    print("\n🚀 API呼び出しテスト実行")
    print("=" * 50)
    
    # API呼び出し
    cmd = [
        'curl', '-X', 'POST', 'http://localhost:8000/api/sessions/start',
        '-H', 'Content-Type: application/json',
        '-d', '{"initial_character": "こ"}',
        '-s'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                fallback_used = data.get('fallbackUsed', True)
                keywords = data.get('keywordCandidates', [])
                session_id = data.get('sessionId', 'unknown')
                
                print("📊 API結果:")
                print(f"  Session ID: {session_id}")
                print(f"  fallbackUsed: {fallback_used}")
                print(f"  Keywords: {keywords}")
                
                if fallback_used:
                    print("⚠️  まだフォールバックが使用されています")
                else:
                    print("✅ LLM動的生成が成功！")
                
                return fallback_used
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")
                print(f"Raw response: {result.stdout}")
                return None
        else:
            print(f"❌ API呼び出しエラー: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ API呼び出し例外: {e}")
        return None

def check_log_file():
    """ログファイルの内容を確認"""
    log_file = "logs/nightloom.log"
    
    print(f"\n📋 ログファイル確認: {log_file}")
    print("=" * 60)
    
    try:
        if not os.path.exists(log_file):
            print("❌ ログファイルが見つかりません")
            print("   サーバーがログファイル出力設定で起動されていない可能性があります")
            return
            
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("⚠️  ログファイルが空です")
            return
            
        print(f"📄 ログ行数: {len(lines)}")
        
        # 最近のAPI関連ログを抽出
        recent_lines = []
        for line in reversed(lines):
            if any(keyword in line for keyword in ['Provider Chain', 'Health Check', 'Mock', 'API', 'bootstrap']):
                recent_lines.append(line.strip())
                if len(recent_lines) >= 20:  # 最新20行
                    break
        
        if recent_lines:
            print("\n🔍 関連ログ (最新順):")
            print("-" * 60)
            for line in reversed(recent_lines):
                # ログレベルに応じてプレフィックスを設定
                if 'ERROR' in line:
                    prefix = "❌ "
                elif 'WARN' in line:
                    prefix = "⚠️  "
                elif '✓ Success' in line:
                    prefix = "✅ "
                elif 'Provider Chain' in line:
                    prefix = "🔗 "
                elif 'Health Check' in line:
                    prefix = "🏥 "
                elif 'Mock' in line:
                    prefix = "🎭 "
                else:
                    prefix = "📝 "
                
                print(f"{prefix}{line}")
        else:
            print("⚠️  関連するログエントリが見つかりません")
            
        # エラーパターンの確認
        error_count = sum(1 for line in lines if 'ERROR' in line)
        warn_count = sum(1 for line in lines if 'WARN' in line)
        
        print(f"\n📊 ログサマリー:")
        print(f"  エラー: {error_count}件")
        print(f"  警告: {warn_count}件")
        
        if error_count > 0:
            print("  ❌ エラーが検出されました - 詳細確認が必要です")
        elif warn_count > 0:
            print("  ⚠️  警告が検出されました")
        else:
            print("  ✅ エラー・警告なし")
            
    except Exception as e:
        print(f"❌ ログファイル読み取りエラー: {e}")

def main():
    print("🔧 NightLoom サーバー待機 & ログ確認テスト")
    print("=" * 80)
    print(f"開始時刻: {datetime.now()}")
    print()
    
    # 1. サーバー起動待機
    if not wait_for_server():
        print("\n❌ サーバーが起動していません。")
        print("手動で以下のコマンドでサーバーを起動してください:")
        print("cd backend")
        print("LOG_LEVEL=DEBUG OPENAI_LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # 2. API呼び出しテスト
    fallback_used = test_api_and_check_logs()
    
    # 3. ログファイル確認
    print("\n⏳ ログ出力待機...")
    time.sleep(3)  # ログ出力のための待機
    check_log_file()
    
    # 4. 結果判定
    print("\n" + "=" * 80)
    print("🎯 最終結果")
    print("=" * 80)
    
    if fallback_used is None:
        print("❌ API呼び出しに失敗しました")
    elif fallback_used:
        print("⚠️  fallbackUsed: true - 修正が完全ではありません")
        print("   ログファイルでエラーの詳細を確認してください")
    else:
        print("🎉 fallbackUsed: false - 修正が成功しています！")
        print("   LLMによる動的キーワード生成が正常に動作中")
    
    print(f"\n📋 継続監視:")
    print(f"   tail -f {os.path.abspath('logs/nightloom.log')}")

if __name__ == "__main__":
    main()

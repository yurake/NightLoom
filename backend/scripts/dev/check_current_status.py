#!/usr/bin/env python3
"""
現在のサーバー状態とエラーを詳細に調査するスクリプト

実際にAPI呼び出しを行い、その結果とサーバーログのエラーパターンを分析します。
"""

import subprocess
import json
import time
from datetime import datetime

def run_curl_test():
    """curlコマンドでAPIテストを実行"""
    print("🔧 curl コマンドでのテスト実行")
    print("=" * 50)
    
    cmd = [
        'curl', '-X', 'POST', 'http://localhost:8000/api/sessions/start',
        '-H', 'Content-Type: application/json',
        '-d', '{"initial_character": "お"}',
        '-s'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print("✅ API呼び出し成功")
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                fallback_used = data.get('fallbackUsed', True)
                print()
                print(f"🎯 重要: fallbackUsed = {fallback_used}")
                
                if fallback_used:
                    print("❌ まだフォールバックが使用されています - 問題が残存")
                    return False
                else:
                    print("✅ LLM動的生成が成功しています")
                    return True
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")
                print(f"Raw response: {result.stdout}")
                return False
        else:
            print(f"❌ curl エラー (exit code: {result.returncode})")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API呼び出しタイムアウト")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def check_server_status():
    """サーバーの基本的な状態を確認"""
    print("\n🌐 サーバー状態確認")
    print("=" * 50)
    
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:8000/health'], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ サーバーは起動中")
            print(f"Health check response: {result.stdout}")
        else:
            print("❌ サーバーが応答しません")
            return False
            
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    return True

def analyze_possible_issues():
    """考えられる問題点を分析"""
    print("\n🔍 問題分析")
    print("=" * 50)
    
    issues = [
        "1. サーバーの自動リロードが正しく動作していない",
        "2. 修正したファイルがサーバーに反映されていない",
        "3. 新しいエラーが発生している",
        "4. インポートエラーが発生している",
        "5. 設定の問題でプロバイダーが正常に動作していない"
    ]
    
    for issue in issues:
        print(f"  • {issue}")
    
    print("\n💡 推奨される対処法:")
    print("  1. サーバーを手動で再起動")
    print("  2. Python環境の確認")
    print("  3. インポートエラーのチェック")
    print("  4. 設定ファイルの確認")

def main():
    print("🚀 NightLoom LLM Health Check 詳細診断")
    print("=" * 80)
    print(f"診断開始時刻: {datetime.now()}")
    print()
    
    # 1. サーバー状態確認
    if not check_server_status():
        print("\n❌ サーバーが起動していません。サーバーを起動してから再試行してください。")
        return
    
    # 2. API テスト実行
    api_success = run_curl_test()
    
    # 3. 結果分析
    print("\n" + "=" * 80)
    print("📊 診断結果")
    print("=" * 80)
    
    if api_success:
        print("🎉 修正は成功しています！")
        print("   fallbackUsed: false が確認されました。")
    else:
        print("⚠️  まだ問題が残っています。")
        print("   詳細なサーバーログを確認する必要があります。")
        analyze_possible_issues()
    
    print("\n🔧 次のステップ:")
    if not api_success:
        print("  1. サーバーのターミナルでリアルタイムログを確認")
        print("  2. 具体的なエラーメッセージを特定")
        print("  3. 該当するコードを修正")
    else:
        print("  修正完了！LLM機能が正常に動作しています。")

if __name__ == "__main__":
    main()

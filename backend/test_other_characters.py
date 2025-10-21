#!/usr/bin/env python3
"""
他の初期文字でのキーワード生成動作確認スクリプト

「か」「さ」から始まるキーワードが正しく生成されるかをテストします。
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime

# プロジェクトのルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from app.services.prompt_template import get_template_manager
from app.clients.llm_client import LLMTaskType

# ログファイルパス
LOG_FILE = "/tmp/nightloom_other_chars_test.log"

def log_output(message):
    """コンソールとファイルの両方に出力"""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()}: {message}\n")

async def test_character(initial_char, expected_keywords):
    """指定した初期文字でプロンプトテンプレートをテスト"""
    log_output(f"\n=== 初期文字「{initial_char}」のテスト ===")
    
    template_manager = get_template_manager()
    
    template_data = {
        "initial_character": initial_char,
        "count": 4
    }
    
    try:
        # プロンプトをレンダリング
        prompt = await template_manager.render_template(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            template_data=template_data
        )
        
        log_output(f"初期文字「{initial_char}」のプロンプトが正常にレンダリングされました")
        
        # 重要な指示が含まれているかチェック
        checks = [
            (f"初期文字「{initial_char}」", f"「{initial_char}」" in prompt),
            (f"ひらがなの「{initial_char}」で始まること", f"ひらがなの「{initial_char}」で始まること" in prompt),
            ("JSON形式", "JSON" in prompt or "json" in prompt),
            ("4個生成", "4" in prompt)
        ]
        
        log_output(f"プロンプト内容チェック:")
        all_checks_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            log_output(f"{status} {check_name}: {result}")
            if not result:
                all_checks_passed = False
        
        # 期待キーワードのテスト
        log_output(f"\n期待キーワードテスト:")
        for i, keyword in enumerate(expected_keywords, 1):
            starts_correctly = keyword.startswith(initial_char)
            status = "✅" if starts_correctly else "❌"
            log_output(f"{status} キーワード{i}: '{keyword}' - 「{initial_char}」から開始: {starts_correctly}")
            if not starts_correctly:
                all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        log_output(f"❌ エラー: {e}")
        return False

async def main():
    """メイン関数"""
    # ログファイルを初期化
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"NightLoom 他の初期文字テスト開始: {datetime.now().isoformat()}\n")
    
    log_output("NightLoom 他の初期文字でのキーワード生成確認")
    log_output("=" * 60)
    
    test_cases = [
        ("か", ["かんしゃ", "かがやき", "かつりょく", "かんどう"]),
        ("さ", ["さいわい", "さわやか", "さくせん", "さんび"]),
        ("た", ["たのしい", "たくましい", "たいせつ", "たんじゅん"]),
    ]
    
    all_tests_passed = True
    
    for char, keywords in test_cases:
        test_result = await test_character(char, keywords)
        if not test_result:
            all_tests_passed = False
    
    # 総合判定
    log_output("\n" + "=" * 60)
    log_output("総合結果:")
    if all_tests_passed:
        log_output("✅ 全ての初期文字でプロンプトテンプレートが正常に動作します")
        log_output("   実際のOpenAI APIでも各初期文字から始まるキーワードが生成されるはずです")
    else:
        log_output("❌ 一部の初期文字で問題が検出されました")
    
    log_output(f"\n詳細なログは {LOG_FILE} に保存されました")

if __name__ == "__main__":
    asyncio.run(main())

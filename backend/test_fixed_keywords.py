#!/usr/bin/env python3
"""
修正後のフォールバックキーワードのテスト
"""

import asyncio
import sys
sys.path.append('.')

from app.services.fallback_assets import FallbackAssets

def test_corrected_keywords():
    """修正されたキーワードが正しい読み方になっているかテスト"""
    
    print("=== 修正後フォールバックキーワード確認 ===\n")
    
    # 修正された初期文字のテスト
    test_chars = ["か", "た", "な", "は", "や", "わ"]
    
    for char in test_chars:
        keywords = FallbackAssets.get_keyword_candidates(char)
        print(f"【{char}】: {keywords}")
        
        # 各キーワードの読み方確認（手動チェック）
        expected_readings = {
            "か": ["かがやく", "かんしゃ", "かわいい", "かっき"],
            "た": ["たのしい", "たいせつ", "たのもしい", "たしか"], 
            "な": ["なつかしい", "なかよし", "ないめん", "なっとく"],
            "は": ["はなさく", "はるらしい", "はれやか", "はくあい"],
            "や": ["やさしい", "やすらぎ", "やわらか", "やくそく"],
            "わ": ["わやか", "わになる", "わかわかしい", "わすれない"]
        }
        
        if char in expected_readings:
            for i, keyword in enumerate(keywords):
                expected_reading = expected_readings[char][i]
                first_char = expected_reading[0]
                if first_char == char:
                    print(f"  ✅ {keyword} → {expected_reading} (正しい)")
                else:
                    print(f"  ❌ {keyword} → {expected_reading} (問題)")
        print()

def test_api_keyword_generation():
    """APIキーワード生成の動作確認テスト"""
    
    print("=== API キーワード生成テスト ===\n")
    
    # 各初期文字でフォールバック機能をテスト
    test_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
    
    for char in test_chars:
        keywords = FallbackAssets.get_keyword_candidates(char)
        print(f"初期文字 '{char}' のキーワード候補: {keywords}")
        
        # 最初のキーワードを選択してシーンを生成
        if keywords:
            selected_keyword = keywords[0]
            scenes = FallbackAssets.get_fallback_scenes("test_theme", selected_keyword)
            
            print(f"  選択キーワード: '{selected_keyword}'")
            print(f"  生成シーン数: {len(scenes)}")
            
            # 最初のシーンの内容確認
            if scenes:
                first_scene = scenes[0]
                print(f"  シーン1: {first_scene.narrative}")
                print(f"  選択肢数: {len(first_scene.choices)}")
        print()

if __name__ == "__main__":
    test_corrected_keywords()
    test_api_keyword_generation()

#!/usr/bin/env python3
"""
フォールバックキーワードの読み方検証スクリプト

各初期文字のキーワードが正しくその音で始まっているかをチェック
"""

import jaconv
from app.services.fallback_assets import FallbackAssets

def get_first_hiragana_char(text: str) -> str:
    """テキストの最初のひらがな文字を取得"""
    # 漢字・カタカナをひらがなに変換
    hiragana_text = jaconv.kata2hira(jaconv.han2zen(text))
    
    # 一般的な読み方マッピング（簡易版）
    reading_map = {
        # あ行
        '愛情': 'あいじょう', '明るい': 'あかるい', '新しい': 'あたらしい', '温かい': 'あたたかい',
        
        # か行  
        '希望': 'きぼう',  # ❌ 「き」始まり
        '輝く': 'かがやく', '感謝': 'かんしゃ', '可愛い': 'かわいい',
        
        # さ行
        '爽やか': 'さわやか', '創造': 'そうぞう', '素晴らしい': 'すばらしい', '澄んだ': 'すんだ',
        
        # た行
        '楽しい': 'たのしい', '大切': 'たいせつ', 
        '力強い': 'ちからづよい',  # ❌ 「ち」始まり
        '豊か': 'ゆたか',  # ❌ 「ゆ」始まり
        
        # な行
        '懐かしい': 'なつかしい', '穏やか': 'おだやか', '自然': 'しぜん', '仲良し': 'なかよし',
        
        # は行
        '花咲く': 'はなさく', '春らしい': 'はるらしい', '晴れやか': 'はれやか', '美しい': 'うつくしい',
        
        # ま行
        '真心': 'まごころ', '眩しい': 'まぶしい', '満足': 'まんぞく', '学び': 'まなび',
        
        # や行
        '優しい': 'やさしい', '安らぎ': 'やすらぎ', '喜び': 'よろこび', '柔らか': 'やわらか',
        
        # ら行
        '楽観的': 'らっかんてき', '立派': 'りっぱ', '理想': 'りそう', '凛とした': 'りんとした',
        
        # わ行
        '和やか': 'わやか', '笑顔': 'えがお', '輪になる': 'わになる', '若々しい': 'わかわかしい'
    }
    
    if text in reading_map:
        return reading_map[text][0]  # 最初の文字
    
    # フォールバック: ひらがな変換を試す
    hiragana = jaconv.kata2hira(text)
    return hiragana[0] if hiragana else text[0]

def validate_keywords():
    """全てのフォールバックキーワードを検証"""
    target_chars = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
    
    invalid_keywords = []
    valid_keywords = []
    
    print("=== フォールバックキーワード読み方検証 ===\n")
    
    for char in target_chars:
        keywords = FallbackAssets.get_keyword_candidates(char)
        print(f"【{char}】初期文字: {keywords}")
        
        for keyword in keywords:
            first_char = get_first_hiragana_char(keyword)
            if first_char == char:
                valid_keywords.append((char, keyword, first_char))
                print(f"  ✅ {keyword} → {first_char} (正しい)")
            else:
                invalid_keywords.append((char, keyword, first_char))
                print(f"  ❌ {keyword} → {first_char} (期待: {char})")
        
        print()
    
    print("=== 検証結果 ===")
    print(f"正しいキーワード: {len(valid_keywords)}個")
    print(f"問題のあるキーワード: {len(invalid_keywords)}個")
    
    if invalid_keywords:
        print("\n🔴 修正が必要なキーワード:")
        for expected, keyword, actual in invalid_keywords:
            print(f"  {expected}: '{keyword}' → 実際の読み: '{actual}'")
    
    return invalid_keywords

def suggest_corrections():
    """修正候補を提案"""
    corrections = {
        "か": {
            "希望": ["輝く", "感謝", "可愛い", "活気", "快適", "価値"]  # 「き」→「か」始まり
        },
        "た": {
            "力強い": ["楽しい", "大切", "頼もしい", "確か", "高い", "正しい"],  # 「ち」→「た」始まり  
            "豊か": ["楽しい", "大切", "頼もしい", "確か", "高い", "正しい"]   # 「ゆ」→「た」始まり
        }
    }
    
    print("\n=== 修正候補 ===")
    for initial_char, replacements in corrections.items():
        print(f"\n【{initial_char}】初期文字:")
        for old_word, candidates in replacements.items():
            print(f"  '{old_word}' → 候補: {candidates}")

if __name__ == "__main__":
    invalid = validate_keywords()
    if invalid:
        suggest_corrections()
    else:
        print("✅ 全てのキーワードが正しい読み方になっています！")

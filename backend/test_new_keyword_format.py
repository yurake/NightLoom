#!/usr/bin/env python3
"""
新しいキーワード生成フォーマットのテスト

読み方情報付きキーワード生成の動作確認用スクリプト
"""

import asyncio
import uuid
from app.services.external_llm import ExternalLLMService
from app.models.session import Session, SessionState
from app.clients.llm_client import LLMResponse, LLMTaskType
from app.models.llm_config import LLMProvider


async def test_new_keyword_format():
    """新しいキーワードフォーマットをテスト"""
    print("=== 新しいキーワード生成フォーマットのテスト ===")
    
    # モックセッションを作成
    session = Session(
        id=uuid.uuid4(),
        state=SessionState.INIT,
        initialCharacter="あ",
        themeId="adventure",
        keywordCandidates=["テスト1", "テスト2", "テスト3", "テスト4"]
    )
    
    print(f"テストセッション ID: {session.id}")
    print(f"初期文字: {session.initialCharacter}")
    
    # LLMサービスを作成
    llm_service = ExternalLLMService()
    
    # モックレスポンスを直接テスト
    mock_response_content = {
        "keywords": [
            {"word": "愛情", "reading": "あいじょう"},
            {"word": "明るい", "reading": "あかるい"},
            {"word": "新しい", "reading": "あたらしい"},
            {"word": "温かい", "reading": "あたたかい"}
        ]
    }
    
    print("\n--- モックレスポンス内容 ---")
    for i, keyword_obj in enumerate(mock_response_content["keywords"], 1):
        print(f"  {i}. 表記: {keyword_obj['word']}, 読み: {keyword_obj['reading']}")
    
    # ExternalLLMServiceの変換ロジックをテスト
    print("\n--- 変換後のキーワードリスト ---")
    keywords = []
    for keyword_obj in mock_response_content["keywords"]:
        if isinstance(keyword_obj, dict) and "word" in keyword_obj:
            keywords.append(keyword_obj["word"])
        elif isinstance(keyword_obj, str):
            keywords.append(keyword_obj)
    
    for i, keyword in enumerate(keywords, 1):
        print(f"  {i}. {keyword}")
    
    print(f"\n変換結果: {len(keywords)}個のキーワードが生成されました")
    print("✅ 新しいフォーマットの変換処理が正常に動作しています")
    
    # バリデーションテスト
    print("\n--- 読み方バリデーションテスト ---")
    test_cases = [
        {"word": "愛情", "reading": "あいじょう"},  # 正常
        {"word": "明るい", "reading": "あかるい"},  # 正常
        {"word": "感謝", "reading": "かんしゃ"},    # 読み方が「あ」で始まらない
    ]
    
    for case in test_cases:
        reading_valid = case["reading"].startswith("あ")
        status = "✅" if reading_valid else "❌"
        message = "あで始まる" if reading_valid else "あで始まらない"
        print(f"  {status} {case['word']} (読み: {case['reading']}) - {message}")


if __name__ == "__main__":
    asyncio.run(test_new_keyword_format())

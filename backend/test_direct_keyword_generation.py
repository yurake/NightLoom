#!/usr/bin/env python3
"""
直接テスト: 新しいキーワード生成の動作確認
"""
import asyncio
import os
from app.services.external_llm import ExternalLLMService, get_llm_service
from app.models.llm_config import LLMConfig
from app.models.session import Session, SessionState
import uuid
from datetime import datetime, timezone

async def test_direct_keyword_generation():
    """新しい実装を直接テストする"""
    print("=== 新しいキーワード生成の直接テスト ===")
    
    # OpenAI APIキーを設定（環境変数から）
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("WARNING: OPENAI_API_KEY環境変数が設定されていません")
        print("フォールバック機能をテストします")
    else:
        print(f"OpenAI API Key設定済み (先頭4文字: {api_key[:4]}...)")
    
    # テストセッションを作成
    session = Session(
        id=uuid.uuid4(),
        state=SessionState.INIT,
        initialCharacter="あ",
        themeId="adventure",
        fallbackFlags=[],
        createdAt=datetime.now(timezone.utc)
    )
    
    print(f"テストセッション作成: {session.id}")
    print(f"初期文字: '{session.initialCharacter}'")
    
    # ExternalLLMServiceのインスタンスを取得
    service = get_llm_service()
    
    try:
        print("\n--- キーワード生成を実行 ---")
        keywords = await service.generate_keywords(session)
        
        print(f"生成されたキーワード: {keywords}")
        print(f"キーワード数: {len(keywords)}")
        print(f"フォールバックフラグ: {session.fallbackFlags}")
        
        # 新しい形式のキーワードが生成されているかチェック
        expected_new_format = all(
            len(keyword) >= 2 and not keyword in ["愛", "冒険", "挑戦", "成長"]
            for keyword in keywords
        )
        
        if expected_new_format:
            print("✅ 新しい形式のキーワードが生成されています")
        else:
            print("❌ 古い形式のキーワードが生成された可能性があります")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_keyword_generation())

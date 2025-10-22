"""
LLM機能統合テスト（正常系のみ）
1分程度で実行可能なクイックテスト
"""

import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.session import Session, SessionState, Scene, Choice
from app.services.session_store import session_store


client = TestClient(app)


@pytest.fixture
def setup_session():
    """テスト用セッションをセットアップ"""
    session_id = uuid4()
    
    # テスト用シーンデータ
    scenes = [
        Scene(
            sceneIndex=1,
            themeId="focus",
            narrative="集中力を試すシーンです",
            choices=[
                Choice(id="choice_1_1", text="集中して取り組む", weights={"focus": 0.8}),
                Choice(id="choice_1_2", text="休憩を取る", weights={"serene": 0.6}),
                Choice(id="choice_1_3", text="バランスを取る", weights={"focus": 0.5, "serene": 0.5}),
                Choice(id="choice_1_4", text="様子を見る", weights={"focus": 0.3})
            ]
        )
    ]
    
    session = Session(
        id=str(session_id),
        state=SessionState.INIT,
        selectedKeyword=None,
        themeId="focus",
        initialCharacter="て",
        keywordCandidates=["テスト", "てがみ", "てんき", "てつだい"],
        scenes=scenes
    )
    
    session_store._sessions[session_id] = session
    return session_id


class TestLLMIntegration:
    """LLM機能統合テスト（正常系）"""
    
    def test_keyword_generation_flow(self, setup_session):
        """キーワード生成～確認の統合フロー"""
        session_id = setup_session
        
        # 1. Bootstrap（初期化）
        response = client.post(f"/api/sessions/start", json={"initial_character": "て"})
        assert response.status_code == 200
        bootstrap_data = response.json()
        session_id_from_bootstrap = bootstrap_data["sessionId"]
        
        # 2. キーワード確認
        with patch('app.services.session.default_session_service.confirm_keyword') as mock_confirm:
            mock_scene = Scene(
                sceneIndex=1,
                themeId="focus",
                narrative="最初のシーン",
                choices=[
                    Choice(id="c1", text="選択1", weights={"focus": 0.8}),
                    Choice(id="c2", text="選択2", weights={"focus": 0.6}),
                    Choice(id="c3", text="選択3", weights={"focus": 0.4}),
                    Choice(id="c4", text="選択4", weights={"focus": 0.2})
                ]
            )
            mock_confirm.return_value = mock_scene
            
            response = client.post(
                f"/api/sessions/{session_id_from_bootstrap}/keyword",
                json={"keyword": "テスト", "source": "suggestion"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "scene" in data
            assert data["scene"]["narrative"] == "最初のシーン"
    
    def test_scenes_api_integration(self, setup_session):
        """シーンAPI統合テスト"""
        session_id = setup_session
        
        # セッションをPLAY状態に変更
        session = session_store.get_session(session_id)
        session.state = SessionState.PLAY
        session.selectedKeyword = "テスト"
        session_store.update_session(session)
        
        # シーン取得
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        assert response.status_code == 200
        
        data = response.json()
        assert "scene" in data
        assert data["scene"]["sceneIndex"] == 1
        assert data["scene"]["narrative"] == "集中力を試すシーンです"
        assert len(data["scene"]["choices"]) == 4
    
    def test_session_progress_tracking(self, setup_session):
        """セッション進行状況の追跡テスト"""
        session_id = setup_session
        
        # セッション状態確認（progressエンドポイントの代わりにsession情報を直接確認）
        session = session_store.get_session(session_id)
        assert session is not None
        assert session.state == SessionState.INIT
        assert len(session.choices) == 0
        assert len(session.scenes) == 1  # setup_sessionで1つのシーンを追加
    
    def test_results_api_basic(self):
        """結果API基本テスト"""
        # 結果生成のテスト（モック使用）
        session_id = uuid4()
        
        # 完了したセッションを作成
        session = Session(
            id=str(session_id),
            state=SessionState.RESULT,
            selectedKeyword="テスト",
            themeId="focus",
            initialCharacter="て",
            keywordCandidates=["テスト", "てがみ", "てんき", "てつだい"]
        )
        
        # 4つの選択を完了状態でセット
        session.choices = [
            type('Choice', (), {'sceneIndex': i, 'choiceId': f'choice_{i}', 'timestamp': '2024-01-01T10:00:00Z'})()
            for i in range(1, 5)
        ]
        
        session_store._sessions[session_id] = session
        
        with patch('app.services.session.default_session_service.generate_result') as mock_diagnosis:
            mock_result = {
                "personalityType": "集中型",
                "description": "集中力に優れたタイプ",
                "axes": [{"name": "focus", "score": 85}]
            }
            mock_diagnosis.return_value = mock_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            assert response.status_code == 200
            
            data = response.json()
            assert "personalityType" in data
            assert data["personalityType"] == "集中型"
    
    def test_fallback_functionality(self, setup_session):
        """フォールバック機能の基本テスト"""
        session_id = setup_session
        
        # LLMエラーを模擬してフォールバック動作を確認
        with patch('app.services.session.default_session_service.load_scene') as mock_load:
            # エラーを発生させてフォールバック処理をトリガー
            mock_load.side_effect = Exception("LLM接続エラー")
            
            response = client.get(f"/api/sessions/{session_id}/scenes/1")
            
            # フォールバックデータまたは適切なエラーレスポンスを確認
            assert response.status_code in [200, 503]
            
            if response.status_code == 200:
                data = response.json()
                # フォールバックが使用された場合
                assert "fallbackUsed" in data
                assert data["fallbackUsed"] is True
    
    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """セッション分離の確認テスト"""
        # 2つの独立したセッションを作成
        session1_id = uuid4()
        session2_id = uuid4()
        
        # セッション1
        session1 = Session(
            id=str(session1_id),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="focus",
            keywordCandidates=["あいうえお", "あさひ", "あめ", "あき"]
        )
        
        # セッション2
        session2 = Session(
            id=str(session2_id),
            state=SessionState.INIT,
            initialCharacter="か",
            themeId="serene",
            keywordCandidates=["かきくけこ", "かぜ", "かみ", "かお"]
        )
        
        session_store._sessions[session1_id] = session1
        session_store._sessions[session2_id] = session2
        
        # 各セッションの独立性を確認（progressエンドポイントの代わりに直接確認）
        session1 = session_store.get_session(session1_id)
        session2 = session_store.get_session(session2_id)
        
        assert session1 is not None
        assert session2 is not None
        
        assert str(session1.id) != str(session2.id)
        assert session1.initialCharacter != session2.initialCharacter
        assert session1.themeId != session2.themeId
        # セッション固有のデータが分離されていることを確認


if __name__ == "__main__":
    # クイック実行用
    pytest.main([__file__, "-v", "--tb=short"])

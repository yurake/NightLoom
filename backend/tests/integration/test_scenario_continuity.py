"""
T033 [P] [US3] Scenario generation continuity test
"""

import pytest
import httpx
from uuid import uuid4
from backend.app.models.session import Session
from backend.app.services.session_store import SessionStore


@pytest.fixture
async def test_session_with_axes():
    """テスト用セッション（評価軸付き）を作成"""
    session = Session(
        id=uuid4(),
        selected_keyword="冒険",
        axes=[
            {"id": "axis_1", "name": "慎重性", "description": "リスクを慎重に評価する傾向", "direction": "慎重⟷大胆"},
            {"id": "axis_2", "name": "社交性", "description": "他者との関わりを求める傾向", "direction": "内向⟷外向"}
        ]
    )
    SessionStore.set_session(session)
    return session


@pytest.mark.asyncio
async def test_scenario_continuity_across_scenes(httpx_mock, test_session_with_axes):
    """複数シーンでの連続性テスト"""
    # Mock Scene 1 response
    scene1_response = {
        "scene": {
            "scene_index": 1,
            "narrative": "あなたは新しい街を探索中です。未知の路地を発見しました。",
            "choices": [
                {"id": "choice_1_1", "text": "慎重に調査してから進む", "weights": {"axis_1": 1.0, "axis_2": -0.5}},
                {"id": "choice_1_2", "text": "友人を呼んで一緒に探索する", "weights": {"axis_1": 0.0, "axis_2": 1.0}},
                {"id": "choice_1_3", "text": "すぐに進んで冒険する", "weights": {"axis_1": -1.0, "axis_2": 0.0}},
                {"id": "choice_1_4", "text": "引き返して安全な道を選ぶ", "weights": {"axis_1": 0.5, "axis_2": -0.5}}
            ]
        }
    }
    
    # Mock Scene 2 response (should reference Scene 1 choice)
    scene2_response = {
        "scene": {
            "scene_index": 2,
            "narrative": "慎重な調査の結果、興味深い発見をしました。次の行動は？",
            "choices": [
                {"id": "choice_2_1", "text": "発見を詳しく記録する", "weights": {"axis_1": 1.0, "axis_2": -0.5}},
                {"id": "choice_2_2", "text": "専門家に相談する", "weights": {"axis_1": 0.5, "axis_2": 0.5}},
                {"id": "choice_2_3", "text": "すぐに次の探索に向かう", "weights": {"axis_1": -0.5, "axis_2": 0.0}},
                {"id": "choice_2_4", "text": "仲間と情報を共有する", "weights": {"axis_1": 0.0, "axis_2": 1.0}}
            ]
        }
    }
    
    # Mock LLM responses
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(scene1_response)}}],
            "usage": {"total_tokens": 300}
        }
    )
    
    httpx_mock.add_response(
        method="POST", 
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(scene2_response)}}],
            "usage": {"total_tokens": 320}
        }
    )

    async with httpx.AsyncClient() as client:
        # Generate Scene 1
        response1 = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session_with_axes.id),
                "scene_index": 1,
                "keyword": "冒険",
                "axes": [
                    {"id": "axis_1", "name": "慎重性", "description": "リスクを慎重に評価する傾向"},
                    {"id": "axis_2", "name": "社交性", "description": "他者との関わりを求める傾向"}
                ],
                "previous_choices": []
            }
        )
        
        assert response1.status_code == 200
        scene1_data = response1.json()
        
        # Simulate user choice in Scene 1
        user_choice_1 = {
            "scene_index": 1,
            "choice_id": "choice_1_1",
            "text": "慎重に調査してから進む"
        }
        
        # Generate Scene 2 with previous choice
        response2 = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session_with_axes.id),
                "scene_index": 2,
                "keyword": "冒険",
                "axes": [
                    {"id": "axis_1", "name": "慎重性"},
                    {"id": "axis_2", "name": "社交性"}
                ],
                "previous_choices": [user_choice_1]
            }
        )
        
        assert response2.status_code == 200
        scene2_data = response2.json()
        
        # Verify continuity: Scene 2 should reference Scene 1 choice
        scene2_narrative = scene2_data["scene"]["narrative"]
        assert "慎重" in scene2_narrative or "調査" in scene2_narrative, \
            "Scene 2 should reference the cautious choice from Scene 1"
        
        # Verify scene progression
        assert scene1_data["scene"]["scene_index"] == 1
        assert scene2_data["scene"]["scene_index"] == 2
        
        # Verify axes consistency
        for choice in scene2_data["scene"]["choices"]:
            assert "axis_1" in choice["weights"]
            assert "axis_2" in choice["weights"]


@pytest.mark.asyncio 
async def test_scenario_choice_weight_consistency(httpx_mock, test_session_with_axes):
    """選択肢の重み一貫性テスト"""
    mock_response = {
        "scene": {
            "scene_index": 1,
            "narrative": "テストシナリオ",
            "choices": [
                {"id": "choice_1_1", "text": "慎重な選択", "weights": {"axis_1": 1.0, "axis_2": 0.0}},
                {"id": "choice_1_2", "text": "社交的な選択", "weights": {"axis_1": 0.0, "axis_2": 1.0}},
                {"id": "choice_1_3", "text": "大胆な選択", "weights": {"axis_1": -1.0, "axis_2": 0.0}},
                {"id": "choice_1_4", "text": "内向的な選択", "weights": {"axis_1": 0.0, "axis_2": -1.0}}
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(mock_response)}}],
            "usage": {"total_tokens": 250}
        }
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session_with_axes.id),
                "scene_index": 1,
                "keyword": "冒険",
                "axes": [
                    {"id": "axis_1", "name": "慎重性"},
                    {"id": "axis_2", "name": "社交性"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all choices have proper weights
        choices = data["scene"]["choices"]
        assert len(choices) == 4
        
        for choice in choices:
            weights = choice["weights"]
            # Each choice should have weights for all axes
            assert "axis_1" in weights
            assert "axis_2" in weights
            # Weights should be valid floats in range [-1.0, 1.0]
            assert isinstance(weights["axis_1"], (int, float))
            assert isinstance(weights["axis_2"], (int, float))
            assert -1.0 <= weights["axis_1"] <= 1.0
            assert -1.0 <= weights["axis_2"] <= 1.0


@pytest.mark.asyncio
async def test_scenario_generation_with_empty_previous_choices(httpx_mock, test_session_with_axes):
    """空の前回選択での生成テスト"""
    mock_response = {
        "scene": {
            "scene_index": 1,
            "narrative": "これは最初のシーンです。",
            "choices": [
                {"id": "choice_1_1", "text": "選択肢1", "weights": {"axis_1": 0.5, "axis_2": 0.0}},
                {"id": "choice_1_2", "text": "選択肢2", "weights": {"axis_1": 0.0, "axis_2": 0.5}},
                {"id": "choice_1_3", "text": "選択肢3", "weights": {"axis_1": -0.5, "axis_2": 0.0}},
                {"id": "choice_1_4", "text": "選択肢4", "weights": {"axis_1": 0.0, "axis_2": -0.5}}
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(mock_response)}}],
            "usage": {"total_tokens": 200}
        }
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session_with_axes.id),
                "scene_index": 1,
                "keyword": "冒険",
                "axes": [
                    {"id": "axis_1", "name": "慎重性"},
                    {"id": "axis_2", "name": "社交性"}
                ],
                "previous_choices": []  # Empty list
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work fine with empty previous choices
        assert data["scene"]["scene_index"] == 1
        assert len(data["scene"]["choices"]) == 4
        assert "これは最初のシーン" in data["scene"]["narrative"]


@pytest.mark.asyncio
async def test_scenario_generation_with_multiple_previous_choices(httpx_mock, test_session_with_axes):
    """複数の前回選択での生成テスト"""
    mock_response = {
        "scene": {
            "scene_index": 3,
            "narrative": "これまでの慎重で社交的な選択を踏まえて、新たな状況が展開されます。",
            "choices": [
                {"id": "choice_3_1", "text": "これまでの方針を継続", "weights": {"axis_1": 0.8, "axis_2": 0.8}},
                {"id": "choice_3_2", "text": "新しいアプローチを試す", "weights": {"axis_1": -0.2, "axis_2": 0.0}},
                {"id": "choice_3_3", "text": "専門家の意見を求める", "weights": {"axis_1": 0.5, "axis_2": 0.9}},
                {"id": "choice_3_4", "text": "直感で判断する", "weights": {"axis_1": -0.7, "axis_2": -0.3}}
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions", 
        json={
            "choices": [{"message": {"content": str(mock_response)}}],
            "usage": {"total_tokens": 350}
        }
    )

    previous_choices = [
        {"scene_index": 1, "choice_id": "choice_1_1", "text": "慎重に調査してから進む"},
        {"scene_index": 2, "choice_id": "choice_2_2", "text": "専門家に相談する"}
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session_with_axes.id),
                "scene_index": 3,
                "keyword": "冒険",
                "axes": [
                    {"id": "axis_1", "name": "慎重性"},
                    {"id": "axis_2", "name": "社交性"}
                ],
                "previous_choices": previous_choices
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify scene reflects previous choices
        narrative = data["scene"]["narrative"]
        assert "慎重" in narrative or "社交" in narrative, \
            "Narrative should reflect previous cautious and social choices"
        
        assert data["scene"]["scene_index"] == 3
        assert len(data["scene"]["choices"]) == 4

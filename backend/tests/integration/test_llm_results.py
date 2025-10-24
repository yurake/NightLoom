
"""
T042 [P] [US4] Contract test for /api/llm/generate/result endpoint
"""

import pytest
import httpx
from uuid import uuid4
from backend.app.models.session import Session, SessionState, ChoiceRecord
from backend.app.services.session_store import SessionStore
from datetime import datetime, timezone


@pytest.fixture
async def completed_test_session():
    """完了したテスト用セッションを作成"""
    session = Session(
        id=uuid4(),
        state=SessionState.PLAY,
        selected_keyword="成長",
        axes=[
            {"id": "axis_1", "name": "計画性", "description": "物事を計画的に進める傾向", "direction": "直感⟷計画"},
            {"id": "axis_2", "name": "協調性", "description": "他者と協力する傾向", "direction": "独立⟷協調"}
        ],
        choices=[
            ChoiceRecord(sceneIndex=1, choiceId="choice_1_1", timestamp=datetime.now(timezone.utc)),
            ChoiceRecord(sceneIndex=2, choiceId="choice_2_2", timestamp=datetime.now(timezone.utc)),
            ChoiceRecord(sceneIndex=3, choiceId="choice_3_1", timestamp=datetime.now(timezone.utc)),
            ChoiceRecord(sceneIndex=4, choiceId="choice_4_3", timestamp=datetime.now(timezone.utc))
        ],
        rawScores={"axis_1": 2.5, "axis_2": -1.0},
        normalizedScores={"axis_1": 0.625, "axis_2": -0.25}
    )
    SessionStore.set_session(session)
    return session


@pytest.mark.asyncio
async def test_generate_result_contract_success(httpx_mock, completed_test_session):
    """結果生成APIの正常な契約テスト"""
    # Mock LLM response
    mock_response = {
        "type_profiles": [
            {
                "typeId": "growth_planner",
                "typeName": "成長志向の計画家",
                "description": "計画的なアプローチで持続的な成長を追求するタイプ",
                "traits": [
                    "目標設定が得意",
                    "段階的な成長を好む",
                    "リスクを慎重に評価する"
                ],
                "strengths": [
                    "長期的な視点を持っている",
                    "着実に成果を積み重ねる",
                    "学習能力が高い"
                ],
                "growth_areas": [
                    "柔軟性を高める",
                    "直感も大切にする",
                    "時には大胆な行動も必要"
                ],
                "compatibility": {
                    "axis_1": 0.8,
                    "axis_2": 0.3
                }
            }
        ],
        "personality_insights": {
            "dominant_traits": ["計画性", "成長志向"],
            "balance_analysis": "計画性が強く、協調性はやや控えめ",
            "personalized_message": "あなたは「成長」をキーワードに、計画的なアプローチで目標達成を目指すタイプです。"
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{
                "message": {"content": str(mock_response)}
            }],
            "usage": {"total_tokens": 450}
        }
    )

    # API call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(completed_test_session.id),
                "keyword": "成長",
                "axes": [
                    {"id": "axis_1", "name": "計画性", "description": "物事を計画的に進める傾向"},
                    {"id": "axis_2", "name": "協調性", "description": "他者と協力する傾向"}
                ],
                "scores": {"axis_1": 0.625, "axis_2": -0.25},
                "choices": [
                    {"scene_index": 1, "choice_id": "choice_1_1", "text": "計画を立ててから行動"},
                    {"scene_index": 2, "choice_id": "choice_2_2", "text": "慎重に情報収集"},
                    {"scene_index": 3, "choice_id": "choice_3_1", "text": "目標を明確にする"},
                    {"scene_index": 4, "choice_id": "choice_4_3", "text": "着実に前進する"}
                ]
            }
        )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "analysis" in data
    assert "type_profiles" in data["analysis"]
    assert len(data["analysis"]["type_profiles"]) >= 1
    assert "personality_insights" in data["analysis"]
    assert "provider_used" in data
    assert "generation_time_ms" in data


@pytest.mark.asyncio
async def test_generate_result_validation_error():
    """結果生成APIのバリデーションエラーテスト"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "keyword": "成長",
                # session_id missing
                "axes": [{"id": "axis_1", "name": "計画性"}]
            }
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_generate_result_session_not_found():
    """存在しないセッションでのエラーテスト"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(uuid4()),  # Non-existent session
                "keyword": "成長",
                "axes": [{"id": "axis_1", "name": "計画性"}],
                "scores": {"axis_1": 0.5},
                "choices": []
            }
        )

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_generate_result_incomplete_session():
    """未完了セッションでのエラーテスト"""
    # Create incomplete session (missing choices)
    incomplete_session = Session(
        id=uuid4(),
        state=SessionState.PLAY,
        selected_keyword="成長",
        choices=[]  # No choices completed
    )
    SessionStore.set_session(incomplete_session)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(incomplete_session.id),
                "keyword": "成長",
                "axes": [{"id": "axis_1", "name": "計画性"}],
                "scores": {"axis_1": 0.5},
                "choices": []
            }
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INCOMPLETE_SESSION"


@pytest.mark.asyncio
async def test_generate_result_llm_service_unavailable(httpx_mock):
    """LLMサービス利用不可時のテスト"""
    # Create completed session
    completed_session = Session(
        id=uuid4(),
        state=SessionState.PLAY,
        selected_keyword="成長",
        choices=[
            ChoiceRecord(sceneIndex=i, choiceId=f"choice_{i}_1", timestamp=datetime.now(timezone.utc))
            for i in range(1, 5)
        ]
    )
    SessionStore.set_session(completed_session)

    # Mock LLM service error
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        status_code=503
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(completed_session.id),
                "keyword": "成長",
                "axes": [{"id": "axis_1", "name": "計画性"}],
                "scores": {"axis_1": 0.5},
                "choices": [
                    {"scene_index": i, "choice_id": f"choice_{i}_1", "text": "選択肢"}
                    for i in range(1, 5)
                ]
            }
        )

    assert response.status_code == 503
    data = response.json()
    assert data["error_code"] == "LLM_SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_generate_result_with_different_keywords(httpx_mock, completed_test_session):
    """異なるキーワードでの結果生成差異テスト"""
    # Mock responses for different keywords
    love_response = {
        "type_profiles": [{
            "typeId": "compassionate_growth",
            "typeName": "愛情深い成長者",
            "description": "愛情をベースに自他の成長を支援するタイプ"
        }]
    }
    
    adventure_response = {
        "type_profiles": [{
            "typeId": "adventurous_growth", 
            "typeName": "冒険的成長者",
            "description": "新しい挑戦を通じて成長を追求するタイプ"
        }]
    }
    
    # Mock first call (love)
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(love_response)}}],
            "usage": {"total_tokens": 400}
        }
    )
    
    # Mock second call (adventure)
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(adventure_response)}}],
            "usage": {"total_tokens": 420}
        }
    )

    async with httpx.AsyncClient() as client:
        # Test with "愛" keyword
        response1 = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(completed_test_session.id),
                "keyword": "愛",
                "axes": [{"id": "axis_1", "name": "計画性"}],
                "scores": {"axis_1": 0.5},
                "choices": [
                    {"scene_index": 1, "choice_id": "choice_1_1", "text": "愛情を示す"}
                ]
            }
        )
        
        # Test with "冒険" keyword
        response2 = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(completed_test_session.id),
                "keyword": "冒険",
                "axes": [{"id": "axis_1", "name": "計画性"}],
                "scores": {"axis_1": 0.5},
                "choices": [
                    {"scene_index": 1, "choice_id": "choice_1_1", "text": "冒険に出る"}
                ]
            }
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should be different based on keywords
        type1 = data1["analysis"]["type_profiles"][0]["typeName"]
        type2 = data2["analysis"]["type_profiles"][0]["typeName"]
        
        assert type1 != type2, "Different keywords should produce different type analyses"
        assert "愛情" in type1, "Love keyword should influence type name"
        assert "冒険" in type2, "Adventure keyword should influence type name"


@pytest.mark.asyncio
async def test_generate_result_with_extreme_scores(httpx_mock, completed_test_session):
    """極端なスコアパターンでの結果生成テスト"""
    extreme_response = {
        "type_profiles": [{
            "typeId": "extreme_planner",
            "typeName": "極限計画家",
            "description": "計画性が極めて高く、独立性も強いタイプ",
            "traits": ["超計画的", "完全独立", "リスク回避"],
            "analysis_notes": "両軸で極端な値を示しており、非常にユニークな特性"
        }],
        "personality_insights": {
            "extreme_patterns": ["計画性: 最高レベル", "協調性: 最低レベル"],
            "balance_note": "極端なバランス状態"
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": str(extreme_response)}}],
            "usage": {"total_tokens": 380}
        }
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/result",
            json={
                "session_id": str(completed_test_session.id),
                "keyword": "完璧",
                "axes": [
                    {"id": "axis_1", "name": "計画性"},
                    {"id": "axis_2", "name": "協調性"}
                ],
                "scores": {"axis_1": 1.0, "axis_2": -1.0},  # Extreme scores
                "choices": [
                    {"scene_index": i, "choice_id": f"choice_{i}_extreme", "text": "極端な選択"}
                    for i in range(1, 5)
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle extreme scores appropriately
        analysis = data["analysis"]
        assert "extreme" in analysis["type_profiles"][0]["typeName"].lower() or \
               "極限" in analysis["type_profiles"][0]["typeName"], \
               "Should recognize extreme score patterns"

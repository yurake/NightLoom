"""
T032 [P] [US3] Contract test for /api/llm/generate/scenario endpoint
"""

import pytest
import httpx
from uuid import uuid4
from backend.app.models.session import Session
from backend.app.services.session_store import SessionStore


@pytest.fixture
async def test_session():
    """テスト用セッションを作成"""
    session = Session(
        id=uuid4(),
        selected_keyword="愛情",
        axes=[
            {"id": "axis_1", "name": "感情表現", "description": "感情を表現する傾向"},
            {"id": "axis_2", "name": "行動力", "description": "積極的な行動を取る傾向"}
        ]
    )
    SessionStore.set_session(session)
    return session


@pytest.mark.asyncio
async def test_generate_scenario_contract_success(httpx_mock, test_session):
    """シナリオ生成APIの正常な契約テスト"""
    # Mock LLM response
    mock_response = {
        "scene": {
            "scene_index": 1,
            "narrative": "あなたは友人との待ち合わせに遅刻してしまいました。友人は少し困惑した表情を浮かべています。",
            "choices": [
                {
                    "id": "choice_1_1",
                    "text": "素直に謝罪して理由を説明する",
                    "weights": {"axis_1": 1.0, "axis_2": 0.5}
                },
                {
                    "id": "choice_1_2", 
                    "text": "軽く謝って話題を変える",
                    "weights": {"axis_1": -0.5, "axis_2": 0.0}
                },
                {
                    "id": "choice_1_3",
                    "text": "積極的に代案を提案する", 
                    "weights": {"axis_1": 0.0, "axis_2": 1.0}
                },
                {
                    "id": "choice_1_4",
                    "text": "相手の気持ちを確認してから対応する",
                    "weights": {"axis_1": 0.5, "axis_2": -0.5}
                }
            ]
        }
    }
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{
                "message": {"content": str(mock_response)}
            }],
            "usage": {"total_tokens": 250}
        }
    )

    # API call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(test_session.id),
                "scene_index": 1,
                "keyword": "愛情",
                "axes": [
                    {"id": "axis_1", "name": "感情表現"},
                    {"id": "axis_2", "name": "行動力"}
                ]
            }
        )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "scene" in data
    assert data["scene"]["scene_index"] == 1
    assert len(data["scene"]["choices"]) == 4
    assert "provider_used" in data
    assert "generation_time_ms" in data


@pytest.mark.asyncio
async def test_generate_scenario_validation_error():
    """シナリオ生成APIのバリデーションエラーテスト"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "scene_index": 1,
                # session_id missing
                "keyword": "愛情"
            }
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_generate_scenario_session_not_found():
    """存在しないセッションでのエラーテスト"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(uuid4()),  # Non-existent session
                "scene_index": 1,
                "keyword": "愛情",
                "axes": [{"id": "axis_1", "name": "感情表現"}]
            }
        )

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_generate_scenario_llm_service_unavailable(httpx_mock):
    """LLMサービス利用不可時のテスト"""
    # Mock LLM service error
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        status_code=503
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/llm/generate/scenario",
            json={
                "session_id": str(uuid4()),
                "scene_index": 1,  
                "keyword": "愛情",
                "axes": [{"id": "axis_1", "name": "感情表現"}]
            }
        )

    assert response.status_code == 503
    data = response.json()
    assert data["error_code"] == "LLM_SERVICE_UNAVAILABLE"

"""
Result生成処理の並列リクエスト時にLLM分析が一度のみ実行されることを確認するテスト。
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.session import (
    Axis,
    Choice,
    ChoiceRecord,
    Scene,
    Session,
    SessionState,
    TypeProfile,
)
from app.services.session import default_session_service
from app.services.session_store import session_store


@pytest.mark.asyncio
async def test_generate_result_llm_called_once_with_parallel_requests(monkeypatch):
    """複数クライアントから同時に結果生成を要求してもLLM分析が一度だけ実行されることを確認する。"""
    # Arrange
    session_id = uuid4()
    axes = [
        Axis(
            id="axis_1",
            name="計画性",
            description="物事を計画的に進める傾向",
            direction="直感 ⟷ 計画"
        ),
        Axis(
            id="axis_2",
            name="協調性",
            description="他者と協力する傾向",
            direction="独立 ⟷ 協調"
        ),
    ]

    scenes = []
    for scene_index in range(1, 5):
        choices = [
            Choice(
                id=f"choice_{scene_index}_{i}",
                text=f"選択肢{i}",
                weights={"axis_1": 0.5 - 0.1 * i, "axis_2": -0.3 + 0.1 * i}
            )
            for i in range(1, 5)
        ]
        scenes.append(
            Scene(
                sceneIndex=scene_index,
                themeId="serene",
                narrative=f"シーン{scene_index}のナラティブ",
                choices=choices
            )
        )

    choices = [
        ChoiceRecord(
            sceneIndex=index,
            choiceId=f"choice_{index}_1",
            timestamp=datetime.now(timezone.utc)
        )
        for index in range(1, 5)
    ]

    session = Session(
        id=session_id,
        state=SessionState.PLAY,
        initialCharacter="あ",
        keywordCandidates=["冒険", "共感", "挑戦", "創造"],
        selectedKeyword="冒険",
        themeId="serene",
        axes=axes,
        scenes=scenes,
        choices=choices,
        fallbackFlags=[],
        rawScores={},
        normalizedScores={}
    )

    session_store.create_session(session)

    raw_scores = {"axis_1": 1.5, "axis_2": -0.5}
    normalized_scores = {"axis_1": 75.0, "axis_2": 25.0}

    calculate_mock = AsyncMock(return_value=raw_scores)
    normalize_mock = AsyncMock(return_value=normalized_scores)
    monkeypatch.setattr(default_session_service.scoring_service, "calculate_scores", calculate_mock)
    monkeypatch.setattr(default_session_service.scoring_service, "normalize_scores", normalize_mock)

    profile = TypeProfile(
        name="Adventurer",
        description="未知に飛び込む探索者タイプ",
        keywords=["adventure", "explore"],
        dominantAxes=["axis_1", "axis_2"],
        polarity="Hi-Lo",
    )

    async def analyze_side_effect(_session):
        await asyncio.sleep(0.02)
        return [profile]

    analyze_mock = AsyncMock(side_effect=analyze_side_effect)
    monkeypatch.setattr(default_session_service.external_llm_service, "analyze_results", analyze_mock)

    dominant_axes_mock = MagicMock(return_value=["axis_1", "axis_2"])
    monkeypatch.setattr(default_session_service.typing_service, "get_dominant_axes", dominant_axes_mock)

    # Act
    tasks = [
        default_session_service.generate_result(session_id) for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)

    # Assert
    assert analyze_mock.await_count == 1, "LLM分析が複数回実行されています"
    assert calculate_mock.await_count == 1
    assert normalize_mock.await_count == 1

    for result in results:
        assert result["sessionId"] == str(session_id)
        assert result["type"]["profiles"][0]["name"] == "Adventurer"
        assert not result["type"]["fallbackUsed"]

    # lock クリーンアップ
    default_session_service._result_generation_locks.pop(session_id, None)

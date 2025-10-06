"""Keyword confirmation endpoint skeleton."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/{session_id}/keyword")
async def post_session_keyword(session_id: str) -> dict[str, object]:
    """Accept a seed word and return placeholder scene data."""

    return {
        "sessionId": session_id,
        "seedWord": "",
        "seedScores": {},
        "themeId": "fallback",
        "firstScene": None,
    }

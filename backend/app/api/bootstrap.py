"""Bootstrap endpoint implementation.

This module provides session bootstrap functionality with LLM integration
and fallback support.
"""

import logging
import random
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.session import default_session_service
from ..services.observability import observability

router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# ひらがな候補リスト（一般的なひらがな文字）
HIRAGANA_CANDIDATES = [
    'あ', 'い', 'う', 'え', 'お',
    'か', 'き', 'く', 'け', 'こ', 'が', 'ぎ', 'ぐ', 'げ', 'ご',
    'さ', 'し', 'す', 'せ', 'そ', 'ざ', 'じ', 'ず', 'ぜ', 'ぞ',
    'た', 'ち', 'つ', 'て', 'と', 'だ', 'ぢ', 'づ', 'で', 'ど',
    'な', 'に', 'ぬ', 'ね', 'の',
    'は', 'ひ', 'ふ', 'へ', 'ほ', 'ば', 'び', 'ぶ', 'べ', 'ぼ', 'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ',
    'ま', 'み', 'む', 'め', 'も',
    'や', 'ゆ', 'よ',
    'ら', 'り', 'る', 'れ', 'ろ',
    'わ', 'を', 'ん'
]

class BootstrapRequest(BaseModel):
    initial_character: Optional[str] = None


@router.post("/start")
async def start_session(request: Optional[BootstrapRequest] = None) -> dict[str, object]:
    """Create a new session with bootstrap data."""
    try:
        initial_character = None
        if request and request.initial_character:
            # Validate initial character length
            if len(request.initial_character) > 1:
                initial_character = "あ"  # Use fallback for invalid character
            else:
                initial_character = request.initial_character
        else:
            # initial_character が None または未指定の場合、ランダムにひらがな文字を選択
            initial_character = random.choice(HIRAGANA_CANDIDATES)
        
        logger.info(f"[API] Starting session with initial_character: {initial_character}")
        
        # Create session using service
        session = await default_session_service.start_session(initial_character)
        
        # Log session start for observability (after session creation)
        observability.log_session_start(session.id, session.initialCharacter, session.themeId)
        
        # Return bootstrap data in expected format
        result = {
            "sessionId": str(session.id),
            "axes": [axis.model_dump() for axis in session.axes],
            "keywordCandidates": session.keywordCandidates,
            "initialCharacter": session.initialCharacter,
            "themeId": session.themeId,
            "fallbackUsed": len(session.fallbackFlags) > 0
        }
        
        logger.info(f"[API] Session start response: sessionId={result['sessionId']}, keywordCandidates={result['keywordCandidates']}, fallbackUsed={result['fallbackUsed']}")
        
        return result
    except Exception as e:
        logger.error(f"[API] Session start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

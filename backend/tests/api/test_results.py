
"""Test suite for result retrieval endpoints - User Story 3 Contract Tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

from app.main import app
from app.models.session import Session, SessionState, AxisScore, TypeProfile

client = TestClient(app)


class TestResultRetrieval:
    """Contract tests for POST /api/sessions/{sessionId}/result."""

    def test_get_result_completed_session(self):
        """Test retrieving result for a completed 4-scene session."""
        session_id = str(uuid.uuid4())
        
        # Mock completed session with all scenes finished
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,  # Will transition to RESULT during result generation
            selectedKeyword="完了",
            themeId="adventure",
            initialCharacter="か",
            keywordCandidates=["完了", "かんしゃ", "かいけつ", "かつやく"]
        )
        
        # Add 4 completed choice records
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_2',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        # Mock result data
        mock_axes = [
            AxisScore(axisId="curiosity", score=75.5, rawScore=2.5),
            AxisScore(axisId="logic", score=45.2, rawScore=-0.8),
            AxisScore(axisId="creativity", score=88.9, rawScore=3.8)
        ]
        
        mock_type_profiles = [
            TypeProfile(
                name="Explorer",
                description="好奇心旺盛で新しい体験を求める",
                keywords=["冒険", "発見", "挑戦"],
                dominantAxes=["curiosity", "creativity"],
                polarity="Hi-Lo",
                meta={"cell": "A1", "isNeutral": False}
            ),
            TypeProfile(
                name="Innovator", 
                description="創造的で革新的なアプローチを取る",
                keywords=["創造", "革新", "独創"],
                dominantAxes=["creativity", "curiosity"],
                polarity="Hi-Hi",
                meta={"cell": "A2", "isNeutral": False}
            ),
            TypeProfile(
                name="Dreamer",
                description="想像力豊かで理想を追求する",
                keywords=["夢", "理想", "想像"],
                dominantAxes=["creativity", "curiosity"],
                polarity="Hi-Mid",
                meta={"cell": "B1", "isNeutral": False}
            ),
            TypeProfile(
                name="Visionary",
                description="未来を見据えた大胆な発想を持つ",
                keywords=["未来", "ビジョン", "革命"],
                dominantAxes=["curiosity", "creativity"],
                polarity="Hi-Hi",
                meta={"cell": "A3", "isNeutral": False}
            )
        ]
        
        mock_result = {
            "sessionId": session_id,
            "keyword": "完了",
            "axes": [axis.dict() for axis in mock_axes],
            "type": {
                "dominantAxes": ["curiosity", "creativity"],
                "profiles": [profile.dict() for profile in mock_type_profiles],
                "fallbackUsed": False
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": []
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            assert "sessionId" in data
            assert "keyword" in data
            assert "axes" in data
            assert "type" in data
            assert "completedAt" in data
            assert data["sessionId"] == session_id
            assert data["keyword"] == "完了"
            
            # Validate axes structure
            axes = data["axes"]
            assert len(axes) >= 2  # Minimum 2 axes
            assert len(axes) <= 6  # Maximum 6 axes
            
            for axis in axes:
                assert "axisId" in axis
                assert "score" in axis
                assert "rawScore" in axis
                assert 0 <= axis["score"] <= 100
                assert -5 <= axis["rawScore"] <= 5
            
            # Validate type structure
            type_data = data["type"]
            assert "dominantAxes" in type_data
            assert "profiles" in type_data
            assert len(type_data["dominantAxes"]) == 2
            assert 4 <= len(type_data["profiles"]) <= 6
            
            # Validate type profiles
            for profile in type_data["profiles"]:
                assert "name" in profile
                assert "description" in profile
                assert "keywords" in profile
                assert "dominantAxes" in profile
                assert "polarity" in profile
                assert len(profile["dominantAxes"]) == 2

    def test_get_result_session_not_found(self):
        """Test result retrieval with non-existent session."""
        session_id = str(uuid.uuid4())
        
        # No session created - session_store should be empty due to autouse fixture
        response = client.post(f"/api/sessions/{session_id}/result")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "SESSION_NOT_FOUND"
        assert "session_id" in data["detail"]["details"]

    def test_get_result_session_not_completed(self):
        """Test result retrieval for session with incomplete scenes."""
        session_id = str(uuid.uuid4())
        
        # Mock session with only 2 scenes completed
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="未完了",
            themeId="focus",
            initialCharacter="み",
            keywordCandidates=["未完了", "みらい", "みっつ", "みんな"]
        )
        
        # Only 2 choice records (need 4 for completion)
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': 1,
                'choiceId': 'choice_1_1',
                'timestamp': datetime.now()
            })(),
            type('ChoiceRecord', (), {
                'sceneIndex': 2,
                'choiceId': 'choice_2_3',
                'timestamp': datetime.now()
            })()
        ]
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["error_code"] == "SESSION_NOT_COMPLETED"
            assert "required_scenes" in data["detail"]["details"]

    def test_get_result_invalid_session_state(self):
        """Test result retrieval for session in INIT state."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.INIT,  # Invalid state for result
            themeId="serene",
            initialCharacter="し",
            keywordCandidates=["しずか", "しんぱい", "しっかり", "しあわせ"]
        )
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["error_code"] == "BAD_REQUEST"

    def test_get_result_llm_service_unavailable_with_fallback(self):
        """Test result retrieval when LLM fails but fallback is available."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="フォールバック",
            themeId="fallback",
            initialCharacter="ふ",
            keywordCandidates=["フォールバック", "ふあん", "ふくざつ", "ふしぎ"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_1',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        # Mock fallback result
        mock_fallback_result = {
            "sessionId": session_id,
            "keyword": "フォールバック",
            "axes": [
                {"axisId": "stability", "score": 50.0, "rawScore": 0.0},
                {"axisId": "adaptability", "score": 50.0, "rawScore": 0.0}
            ],
            "type": {
                "dominantAxes": ["stability", "adaptability"],
                "profiles": [
                    {
                        "name": "Balanced",
                        "description": "バランスの取れた判断をする",
                        "keywords": ["安定", "適応", "バランス"],
                        "dominantAxes": ["stability", "adaptability"],
                        "polarity": "Mid-Mid"
                    },
                    {
                        "name": "Steady",
                        "description": "着実に物事を進める",
                        "keywords": ["着実", "継続", "信頼"],
                        "dominantAxes": ["stability", "adaptability"],
                        "polarity": "Hi-Mid" 
                    },
                    {
                        "name": "Flexible",
                        "description": "状況に応じて柔軟に対応する",
                        "keywords": ["柔軟", "対応", "変化"],
                        "dominantAxes": ["adaptability", "stability"],
                        "polarity": "Mid-Hi"
                    },
                    {
                        "name": "Resilient",
                        "description": "困難に立ち向かう強さを持つ",
                        "keywords": ["回復", "強さ", "耐性"],
                        "dominantAxes": ["stability", "adaptability"],
                        "polarity": "Hi-Hi"
                    }
                ],
                "fallbackUsed": True
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": ["TYPE_FALLBACK", "AXIS_FALLBACK"]
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_fallback_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should include fallback indicators
            assert "fallbackFlags" in data
            assert len(data["fallbackFlags"]) > 0
            assert data["type"]["fallbackUsed"] is True

    def test_get_result_llm_service_complete_failure(self):
        """Test result retrieval when LLM fails and no fallback available."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="失敗",
            themeId="adventure",
            initialCharacter="し",
            keywordCandidates=["失敗", "しんぱい", "しっぱい", "しかた"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_1',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.side_effect = Exception("Complete LLM failure")
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error_code"] == "LLM_SERVICE_UNAVAILABLE"

    def test_get_result_malformed_session_id(self):
        """Test result retrieval with malformed session ID."""
        invalid_session_id = "not-a-uuid"
        
        response = client.post(f"/api/sessions/{invalid_session_id}/result")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    def test_get_result_performance_contract(self):
        """Test that result generation meets performance requirements."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="性能",
            themeId="focus",
            initialCharacter="せ",
            keywordCandidates=["性能", "せいこう", "せんたく", "せいかく"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_{i%4+1}',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        mock_result = {
            "sessionId": session_id,
            "keyword": "性能",
            "axes": [
                {"axisId": "efficiency", "score": 85.0, "rawScore": 3.2},
                {"axisId": "quality", "score": 78.5, "rawScore": 2.8}
            ],
            "type": {
                "dominantAxes": ["efficiency", "quality"],
                "profiles": [
                    {
                        "name": "Optimizer",
                        "description": "効率性を重視して最適化を図る",
                        "keywords": ["効率", "最適化", "改善"],
                        "dominantAxes": ["efficiency", "quality"],
                        "polarity": "Hi-Hi"
                    },
                    {
                        "name": "Perfectionist",
                        "description": "高品質な結果を追求する",
                        "keywords": ["完璧", "品質", "精度"],
                        "dominantAxes": ["quality", "efficiency"],
                        "polarity": "Hi-Hi"
                    },
                    {
                        "name": "Pragmatist",
                        "description": "実用性を重視して判断する",
                        "keywords": ["実用", "現実", "実践"],
                        "dominantAxes": ["efficiency", "quality"],
                        "polarity": "Hi-Mid"
                    },
                    {
                        "name": "Strategist",
                        "description": "戦略的に物事を進める",
                        "keywords": ["戦略", "計画", "効果"],
                        "dominantAxes": ["efficiency", "quality"],
                        "polarity": "Hi-Hi"
                    }
                ],
                "fallbackUsed": False
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": []
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_result
            
            import time
            start_time = time.time()
            response = client.post(f"/api/sessions/{session_id}/result")
            end_time = time.time()
            
            assert response.status_code == 200
            
            # Performance requirement: p95 ≤ 1.2s for result generation
            response_time_ms = (end_time - start_time) * 1000
            assert response_time_ms < 2000, f"Result generation time {response_time_ms:.1f}ms exceeds reasonable limit"


class TestResultDataValidation:
    """Tests for result data structure validation and business logic."""
    
    def test_axis_score_normalization(self):
        """Test that axis scores are properly normalized to 0-100 range."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="正規化",
            themeId="focus",
            initialCharacter="せ",
            keywordCandidates=["正規化", "せいかく", "せいり", "せんたく"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_1',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        # Mock result with edge case scores
        mock_result = {
            "sessionId": session_id,
            "keyword": "正規化",
            "axes": [
                {"axisId": "extreme_high", "score": 100.0, "rawScore": 5.0},
                {"axisId": "extreme_low", "score": 0.0, "rawScore": -5.0},
                {"axisId": "neutral", "score": 50.0, "rawScore": 0.0}
            ],
            "type": {
                "dominantAxes": ["extreme_high", "neutral"],
                "profiles": [
                    {
                        "name": "Extremist",
                        "description": "極端な選択を好む",
                        "keywords": ["極端", "決断", "明確"],
                        "dominantAxes": ["extreme_high", "neutral"],
                        "polarity": "Hi-Mid"
                    },
                    {
                        "name": "Moderate",
                        "description": "バランスを取る",
                        "keywords": ["バランス", "中庸", "調和"],
                        "dominantAxes": ["neutral", "extreme_low"],
                        "polarity": "Mid-Lo"
                    },
                    {
                        "name": "Conservative",
                        "description": "慎重なアプローチを取る",
                        "keywords": ["慎重", "安全", "確実"],
                        "dominantAxes": ["extreme_low", "neutral"],
                        "polarity": "Lo-Mid"
                    },
                    {
                        "name": "Neutral",
                        "description": "中立的な立場を保つ",
                        "keywords": ["中立", "客観", "冷静"],
                        "dominantAxes": ["neutral", "extreme_high"],
                        "polarity": "Mid-Hi"
                    }
                ],
                "fallbackUsed": False
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": []
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate score normalization
            for axis in data["axes"]:
                assert 0 <= axis["score"] <= 100, f"Score {axis['score']} not in valid range"
                assert -5 <= axis["rawScore"] <= 5, f"Raw score {axis['rawScore']} not in valid range"

    def test_type_profile_count_validation(self):
        """Test that type profiles are within valid count range (4-6)."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="プロファイル",
            themeId="serene",
            initialCharacter="ぷ",
            keywordCandidates=["プロファイル", "ぷらん", "ぷろ", "ぷろせす"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_2',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        # Mock result with 5 profiles
        mock_result = {
            "sessionId": session_id,
            "keyword": "プロファイル",
            "axes": [
                {"axisId": "openness", "score": 72.0, "rawScore": 2.2},
                {"axisId": "structure", "score": 38.5, "rawScore": -1.1}
            ],
            "type": {
                "dominantAxes": ["openness", "structure"],
                "profiles": [
                    {"name": f"Type{i}", "description": f"説明{i}", "keywords": [f"キー{i}"],
                     "dominantAxes": ["openness", "structure"], "polarity": "Hi-Lo"}
                    for i in range(1, 6)  # 5 profiles
                ],
                "fallbackUsed": False
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": []
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate profile count
            profile_count = len(data["type"]["profiles"])
            assert 4 <= profile_count <= 6, f"Profile count {profile_count} not in valid range"

    def test_dominant_axes_consistency(self):
        """Test that dominant axes are consistent between type and axes data."""
        session_id = str(uuid.uuid4())
        
        mock_session = Session(
            id=session_id,
            state=SessionState.PLAY,
            selectedKeyword="一貫性",
            themeId="focus",
            initialCharacter="い",
            keywordCandidates=["一貫性", "いみ", "いしき", "いそう"]
        )
        
        # 4 completed scenes
        mock_session.choices = [
            type('ChoiceRecord', (), {
                'sceneIndex': i,
                'choiceId': f'choice_{i}_3',
                'timestamp': datetime.now()
            })()
            for i in range(1, 5)
        ]
        
        mock_result = {
            "sessionId": session_id,
            "keyword": "一貫性",
            "axes": [
                {"axisId": "consistency", "score": 82.0, "rawScore": 3.1},
                {"axisId": "flexibility", "score": 35.5, "rawScore": -1.4},
                {"axisId": "reliability", "score": 90.0, "rawScore": 4.2}
            ],
            "type": {
                "dominantAxes": ["consistency", "reliability"],
                "profiles": [
                    {
                        "name": "Reliable",
                        "description": "信頼性の高い判断をする",
                        "keywords": ["信頼", "一貫", "安定"],
                        "dominantAxes": ["reliability", "consistency"],
                        "polarity": "Hi-Hi"
                    },
                    {
                        "name": "Steady",
                        "description": "着実に物事を進める",
                        "keywords": ["着実", "継続", "堅実"],
                        "dominantAxes": ["consistency", "reliability"],
                        "polarity": "Hi-Hi"
                    },
                    {
                        "name": "Methodical",
                        "description": "系統立てて取り組む",
                        "keywords": ["系統", "方法", "順序"],
                        "dominantAxes": ["consistency", "reliability"],
                        "polarity": "Hi-Hi"
                    },
                    {
                        "name": "Disciplined",
                        "description": "規律正しくアプローチする",
                        "keywords": ["規律", "秩序", "統制"],
                        "dominantAxes": ["reliability", "consistency"],
                        "polarity": "Hi-Hi"
                    }
                ],
                "fallbackUsed": False
            },
            "completedAt": datetime.now().isoformat(),
            "fallbackFlags": []
        }
        
        with patch('app.services.session_store.SessionStore.get_session') as mock_get, \
             patch('app.services.session.SessionService.generate_result') as mock_generate:
            
            mock_get.return_value = mock_session
            mock_generate.return_value = mock_result
            
            response = client.post(f"/api/sessions/{session_id}/result")
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate dominant axes exist in axes list
            axes_ids = [axis["axisId"] for axis in data["axes"]]
            dominant_axes = data["type"]["dominantAxes"]
            
            for dominant_axis in dominant_axes:
                assert dominant_axis in axes_ids, f"Dominant axis {dominant_axis} not found in axes data"

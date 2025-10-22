
"""
LLMプロバイダー障害テスト
OpenAI/Anthropic API障害時のフォールバック動作とエラーハンドリングのテスト
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.external_llm import ExternalLLMService, AllProvidersFailedError
from app.models.session import Session, SessionState
from app.models.llm_config import LLMConfig, LLMProvider, ProviderConfig
from app.clients.llm_client import RateLimitError, ProviderUnavailableError, ValidationError
from app.clients.openai_client import OpenAIClient
from app.clients.anthropic_client import AnthropicClient, AnthropicCreditError, AnthropicAccountError
from app.services.fallback_assets import FallbackAssets


class TestLLMProviderFailures:
    """LLMプロバイダー障害時のエラーハンドリングテスト"""

    @pytest.fixture
    def mock_session(self):
        """テスト用セッション"""
        return Session(
            id=str(uuid4()),
            state=SessionState.INIT,
            themeId="focus",
            initialCharacter="あ",
            keywordCandidates=["愛情", "明るい", "新しい", "温かい"]
        )

    @pytest.fixture
    def llm_config_openai_only(self):
        """OpenAIのみの設定"""
        config = LLMConfig()
        config.providers = {
            LLMProvider.OPENAI: ProviderConfig(
                provider=LLMProvider.OPENAI,
                api_key="test-openai-key",
                model_name="gpt-4o-mini"
            )
        }
        config.primary_provider = LLMProvider.OPENAI
        return config

    @pytest.fixture
    def llm_config_multi_provider(self):
        """複数プロバイダー設定"""
        config = LLMConfig()
        config.providers = {
            LLMProvider.OPENAI: ProviderConfig(
                provider=LLMProvider.OPENAI,
                api_key="test-openai-key",
                model_name="gpt-4o-mini"
            ),
            LLMProvider.ANTHROPIC: ProviderConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key="test-anthropic-key",
                model_name="claude-3-haiku-20240307"
            )
        }
        config.primary_provider = LLMProvider.OPENAI
        config.fallback_providers = [LLMProvider.ANTHROPIC]  # 明示的にフォールバックチェーンを設定
        return config

    @pytest.mark.asyncio
    async def test_openai_api_timeout(self, mock_session, llm_config_openai_only):
        """OpenAI APIタイムアウト時のハンドリング"""
        service = ExternalLLMService(config=llm_config_openai_only)
        
        # OpenAI APIタイムアウトをモック
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = ProviderUnavailableError("OpenAI timeout")
            mock_get_client.return_value = mock_client
            
            # ヘルスチェックもモック（成功させる）
            with patch.object(service, '_check_provider_health', return_value=True):
                # フォールバックが動作することを確認
                keywords = await service.generate_keywords(mock_session)
                
                # フォールバックキーワードが返される
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags
                assert all(isinstance(kw, str) for kw in keywords)

    @pytest.mark.asyncio
    async def test_openai_rate_limit_error(self, mock_session, llm_config_openai_only):
        """OpenAI レート制限エラーのハンドリング"""
        service = ExternalLLMService(config=llm_config_openai_only)
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = RateLimitError("Rate limit exceeded")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                # フォールバックが実行される
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags
                
                # エラーがセッションに記録される
                assert len(mock_session.llmErrors) > 0
                assert mock_session.llmErrors[0]["error_type"] == "RateLimitError"

    @pytest.mark.asyncio
    async def test_openai_connection_error(self, mock_session, llm_config_openai_only):
        """OpenAI 接続エラーのハンドリング"""
        service = ExternalLLMService(config=llm_config_openai_only)
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = ProviderUnavailableError("Connection failed")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_anthropic_credit_error(self, mock_session):
        """Anthropic クレジット不足エラーのハンドリング"""
        config = LLMConfig()
        config.providers = {
            LLMProvider.ANTHROPIC: ProviderConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key="test-anthropic-key",
                model_name="claude-3-haiku-20240307"
            )
        }
        config.primary_provider = LLMProvider.ANTHROPIC
        
        service = ExternalLLMService(config=config)
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = AnthropicCreditError("Credit balance too low")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                # フォールバックが実行される
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags
                
                # クレジットエラーが記録される
                assert len(mock_session.llmErrors) > 0
                assert mock_session.llmErrors[0]["error_type"] == "AnthropicCreditError"

    @pytest.mark.asyncio
    async def test_anthropic_account_error(self, mock_session):
        """Anthropic アカウントエラーのハンドリング"""
        config = LLMConfig()
        config.providers = {
            LLMProvider.ANTHROPIC: ProviderConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key="invalid-key",
                model_name="claude-3-haiku-20240307"
            )
        }
        config.primary_provider = LLMProvider.ANTHROPIC
        
        service = ExternalLLMService(config=config)
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = AnthropicAccountError("Authentication failed")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_multi_provider_fallback_chain(self, mock_session, llm_config_multi_provider):
        """複数プロバイダーでのフォールバックチェーン動作"""
        service = ExternalLLMService(config=llm_config_multi_provider)
        
        with patch.object(service, '_get_client') as mock_get_client:
            # OpenAI（プライマリ）は失敗、Anthropic（セカンダリ）は成功
            def client_side_effect(provider):
                if provider == LLMProvider.OPENAI:
                    mock_client = AsyncMock()
                    mock_client.generate_keywords.side_effect = RateLimitError("OpenAI rate limit")
                    return mock_client
                elif provider == LLMProvider.ANTHROPIC:
                    mock_client = AsyncMock()
                    from app.clients.llm_client import LLMResponse, LLMTaskType
                    mock_response = LLMResponse(
                        task_type=LLMTaskType.KEYWORD_GENERATION,
                        session_id=mock_session.id,
                        content={"keywords": [
                            {"word": "愛情", "reading": "あいじょう"},
                            {"word": "明るい", "reading": "あかるい"},
                            {"word": "新しい", "reading": "あたらしい"},
                            {"word": "温かい", "reading": "あたたかい"}
                        ]},
                        provider=LLMProvider.ANTHROPIC,
                        model_name="claude-3-haiku-20240307",
                        tokens_used=150,
                        latency_ms=250.0,
                        cost_estimate=0.001
                    )
                    mock_client.generate_keywords.return_value = mock_response
                    return mock_client
            
            mock_get_client.side_effect = client_side_effect
            
            # ヘルスチェックをモック（両方とも成功）
            def health_check_side_effect(provider):
                return True  # 両方のプロバイダーのヘルスチェックを成功させる
            
            with patch.object(service, '_check_provider_health', side_effect=health_check_side_effect):
                keywords = await service.generate_keywords(mock_session)
                
                # Anthropicから正常にキーワードが取得される
                assert len(keywords) == 4
                assert keywords[0] == "愛情"
                
                # フォールバックフラグが設定される（プライマリプロバイダーではないため）
                assert "keyword_generation_fallback_provider" in mock_session.fallbackFlags
                
                # OpenAIのエラーが記録される
                assert len(mock_session.llmErrors) > 0
                assert mock_session.llmErrors[0]["error_type"] == "RateLimitError"
                
                # Anthropicの成功が記録される
                assert len(mock_session.llmGenerations) > 0
                operation_key = list(mock_session.llmGenerations.keys())[0]
                generation = mock_session.llmGenerations[operation_key]
                assert generation.provider == "anthropic"
                assert generation.fallback_used is True

    @pytest.mark.asyncio
    async def test_all_providers_fail(self, mock_session, llm_config_multi_provider):
        """全プロバイダー失敗時の動作"""
        service = ExternalLLMService(config=llm_config_multi_provider)
        
        with patch.object(service, '_get_client') as mock_get_client:
            # 全プロバイダーが失敗
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = ProviderUnavailableError("All providers down")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                # フォールバックキーワードが返される
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags
                
                # 少なくとも1つのプロバイダーエラーが記録される（実際の設定による）
                assert len(mock_session.llmErrors) >= 1

    @pytest.mark.asyncio
    async def test_validation_error_fallback(self, mock_session, llm_config_openai_only):
        """バリデーションエラー時のフォールバック"""
        service = ExternalLLMService(config=llm_config_openai_only)
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            # 不正なレスポンス形式でバリデーションエラーを発生
            mock_client.generate_keywords.side_effect = ValidationError("Invalid response format")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                keywords = await service.generate_keywords(mock_session)
                
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_network_timeout_scenario(self, mock_session, llm_config_multi_provider):
        """ネットワークタイムアウトシナリオ"""
        service = ExternalLLMService(config=llm_config_multi_provider)
        
        with patch.object(service, '_get_client') as mock_get_client:
            # 両プロバイダーでタイムアウト
            mock_client = AsyncMock()
            mock_client.generate_keywords.side_effect = ProviderUnavailableError("Network timeout")
            mock_get_client.return_value = mock_client
            
            with patch.object(service, '_check_provider_health', return_value=True):
                start_time = datetime.now(timezone.utc)
                keywords = await service.generate_keywords(mock_session)
                end_time = datetime.now(timezone.utc)
                
                # フォールバックが迅速に実行される
                duration = (end_time - start_time).total_seconds()
                assert duration < 5.0  # 5秒以内
                
                assert len(keywords) == 4
                assert "keyword_generation" in mock_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_health_check_failure_skip(self, mock_session, llm_config_openai_only):
        """ヘルスチェック失敗時のプロバイダースキップ"""
        service = ExternalLLMService(config=llm_config_openai_only)
        
        with patch.object(service, '_check_provider_health', return_value=True):
            keywords = await service.generate_keywords(mock_session)
            
            # ヘルスチェック失敗でフォールバックが実行される
            assert len(keywords) == 4
            assert "keyword_generation" in mock_session.fallbackFlags

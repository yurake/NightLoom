# Data Model: NightLoom外部LLMサービス統合

**Branch**: `004-nightloom-llm-openai` | **Date**: 2025-10-20 | **Spec**: [spec.md](spec.md)

## 概要

外部LLMサービス統合に必要な新規エンティティと既存エンティティの拡張を定義する。既存のセッション管理システムとの整合性を保ちながら、LLMプロバイダー管理、プロンプトテンプレート、使用量監視のデータ構造を追加する。

## 新規エンティティ

### LLMProvider

LLM サービスプロバイダーの設定と状態管理

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    MOCK = "mock"

@dataclass
class LLMProvider:
    provider_type: ProviderType
    api_key: Optional[str]
    base_url: Optional[str] = None
    model_name: str = ""
    timeout: float = 5.0
    max_retries: int = 1
    rate_limit_threshold: float = 0.95
    
    # 実行時状態
    is_available: bool = True
    current_usage: int = 0
    rate_limit_max: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        # デフォルトモデル設定
        if self.provider_type == ProviderType.OPENAI:
            self.model_name = self.model_name or "gpt-4-turbo"
        elif self.provider_type == ProviderType.ANTHROPIC:
            self.model_name = self.model_name or "claude-3-sonnet-20240229"
```

**バリデーションルール**:
- `api_key`は本番環境で必須（MOCKは除く）
- `timeout`は1-30秒の範囲
- `rate_limit_threshold`は0.5-1.0の範囲

### PromptTemplate

プロンプトテンプレートの管理と生成

```python
from jinja2 import Template
from typing import Dict, Any, List

@dataclass
class PromptTemplate:
    template_id: str  # "keyword_generation", "axis_creation", etc.
    content: str      # Jinja2テンプレート文字列
    variables: List[str]  # 必須変数リスト
    max_tokens: int = 1000
    temperature: float = 0.7
    version: str = "1.0"
    
    # メタデータ
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def render(self, **kwargs) -> str:
        """テンプレートをレンダリングして実際のプロンプトを生成"""
        template = Template(self.content)
        
        # 必須変数チェック
        missing_vars = set(self.variables) - set(kwargs.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
            
        return template.render(**kwargs)
    
    def validate(self) -> bool:
        """テンプレートの構文チェック"""
        try:
            Template(self.content)
            return True
        except Exception:
            return False
```

**テンプレート種別**:
- `keyword_generation`: 初期文字からキーワード候補生成
- `axis_creation`: キーワードから評価軸生成  
- `scenario_generation`: シーンシナリオ生成
- `result_analysis`: 結果分析生成

### LLMRequest

LLM API呼び出しの記録と追跡

```python
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class LLMRequest:
    request_id: UUID = field(default_factory=uuid4)
    session_id: UUID
    provider_type: ProviderType
    template_id: str
    
    # リクエスト内容
    prompt: str
    model_name: str
    max_tokens: int
    temperature: float
    
    # レスポンス
    response_content: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    
    # 実行結果
    status: str = "pending"  # pending/success/failed/fallback
    error_message: Optional[str] = None
    fallback_used: bool = False
    
    # タイミング
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    def mark_success(self, response: str, tokens: int, cost: float):
        """成功完了をマーク"""
        self.status = "success"
        self.response_content = response
        self.tokens_used = tokens
        self.cost_usd = cost
        self.completed_at = datetime.utcnow()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
    
    def mark_failure(self, error: str, fallback_used: bool = False):
        """失敗をマーク"""
        self.status = "fallback" if fallback_used else "failed"
        self.error_message = error
        self.fallback_used = fallback_used
        self.completed_at = datetime.utcnow()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
```

### APIUsageMetrics

API使用量とコスト監視

```python
@dataclass
class APIUsageMetrics:
    provider_type: ProviderType
    date: str  # YYYY-MM-DD
    
    # 使用量
    request_count: int = 0
    token_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    fallback_count: int = 0
    
    # コスト
    total_cost_usd: float = 0.0
    
    # パフォーマンス
    avg_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    
    # レート制限
    rate_limit_hits: int = 0
    rate_limit_percentage: float = 0.0
    
    def add_request(self, request: LLMRequest):
        """リクエスト結果を集計に追加"""
        self.request_count += 1
        
        if request.status == "success":
            self.success_count += 1
            self.token_count += request.tokens_used or 0
            self.total_cost_usd += request.cost_usd or 0.0
        elif request.status == "failed":
            self.failure_count += 1
        elif request.status == "fallback":
            self.fallback_count += 1
            
        if request.duration_ms:
            # 簡単な移動平均（実装時はより正確な統計処理）
            self.avg_duration_ms = (self.avg_duration_ms + request.duration_ms) / 2
    
    def is_approaching_limit(self, threshold: float = 0.95) -> bool:
        """レート制限に近づいているかチェック"""
        return self.rate_limit_percentage >= threshold
```

## 既存エンティティの拡張

### Session （拡張）

既存のSessionエンティティにLLM統合関連フィールドを追加

```python
# 既存のSessionクラスに以下フィールドを追加

@dataclass
class Session:
    # ... 既存フィールド ...
    
    # LLM統合関連の新規フィールド
    llm_provider: Optional[ProviderType] = None
    llm_requests: List[LLMRequest] = field(default_factory=list)
    total_llm_cost: float = 0.0
    
    def add_llm_request(self, request: LLMRequest):
        """LLMリクエストを記録"""
        self.llm_requests.append(request)
        if request.cost_usd:
            self.total_llm_cost += request.cost_usd
    
    def get_generation_status(self) -> Dict[str, bool]:
        """各生成段階のLLM使用状況を取得"""
        templates_used = {req.template_id for req in self.llm_requests if req.status == "success"}
        return {
            "keywords_generated": "keyword_generation" in templates_used,
            "axes_generated": "axis_creation" in templates_used,
            "scenarios_generated": "scenario_generation" in templates_used,
            "results_generated": "result_analysis" in templates_used
        }
```

## 設定エンティティ

### LLMConfig

アプリケーション全体のLLM設定

```python
@dataclass
class LLMConfig:
    # プロバイダー設定
    primary_provider: ProviderType
    secondary_provider: Optional[ProviderType] = None
    
    # プロバイダー詳細
    providers: Dict[ProviderType, LLMProvider] = field(default_factory=dict)
    
    # テンプレート管理
    templates: Dict[str, PromptTemplate] = field(default_factory=dict)
    
    # グローバル設定
    global_timeout: float = 5.0
    cost_limit_per_session: float = 0.05
    enable_fallback: bool = True
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """環境変数から設定を生成"""
        provider_name = os.getenv('LLM_PROVIDER', 'mock')
        primary_provider = ProviderType(provider_name)
        
        config = cls(primary_provider=primary_provider)
        
        # OpenAI設定
        if openai_key := os.getenv('OPENAI_API_KEY'):
            config.providers[ProviderType.OPENAI] = LLMProvider(
                provider_type=ProviderType.OPENAI,
                api_key=openai_key
            )
        
        # Anthropic設定
        if anthropic_key := os.getenv('ANTHROPIC_API_KEY'):
            config.providers[ProviderType.ANTHROPIC] = LLMProvider(
                provider_type=ProviderType.ANTHROPIC,
                api_key=anthropic_key
            )
        
        return config
```

## データ関係図

```
Session 1:N LLMRequest
Session 1:1 LLMProvider (via llm_provider field)

LLMRequest N:1 PromptTemplate (via template_id)
LLMRequest N:1 LLMProvider (via provider_type)

APIUsageMetrics N:1 LLMProvider (via provider_type)

LLMConfig 1:N LLMProvider
LLMConfig 1:N PromptTemplate
```

## 状態遷移

### LLMRequest状態遷移

```
pending → success (正常完了)
pending → failed (API失敗・タイムアウト)
pending → fallback (失敗後フォールバック使用)
```

### LLMProvider可用性

```
available → unavailable (連続失敗・レート制限)
unavailable → available (復旧検知・時間経過)
```

## バリデーション規則

### LLMProvider
- `api_key`: MOCKプロバイダー以外で必須
- `timeout`: 1.0 ≤ timeout ≤ 30.0
- `rate_limit_threshold`: 0.5 ≤ threshold ≤ 1.0

### PromptTemplate
- `content`: 有効なJinja2テンプレート構文
- `variables`: contentで使用される変数と一致
- `max_tokens`: 1 ≤ max_tokens ≤ 4000

### LLMRequest
- `session_id`: 有効なSession.idと対応
- `cost_usd`: 0 ≤ cost ≤ 1.0 (異常値検知)

### APIUsageMetrics
- `date`: YYYY-MM-DD形式
- `rate_limit_percentage`: 0.0 ≤ percentage ≤ 1.0

## ストレージ戦略

### セッション内一時データ
- `Session.llm_requests`: セッション終了時に破棄
- `LLMRequest.response_content`: セッション内のみ保持

### 設定データ（永続化）
- `PromptTemplate`: ファイルベース（`templates/prompts/`）
- `LLMConfig`: 環境変数 + 設定ファイル

### メトリクス（短期保持）
- `APIUsageMetrics`: 7日間保持後破棄
- ログファイル: ローテーション管理

この設計により、既存のセッション管理システムとの整合性を保ちながら、外部LLMサービスとの統合に必要なデータ構造を提供する。

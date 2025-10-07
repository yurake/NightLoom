# LLM クライアント統合とフェイルオーバー設計

## 概要
LLM 外部 API との統合と、失敗時の再試行・フォールバック機能の詳細設計。

関連 Issue: #5

## アーキテクチャ

### LLM クライアント抽象化

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    FALLBACK = "fallback"

@dataclass
class LLMRequest:
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: float = 5.0

@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    latency_ms: float
    tokens_used: int

class LLMClient(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """LLM に推論を依頼"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """サービスが利用可能か確認"""
        pass
```

### 再試行制御

```python
from typing import Optional

@dataclass
class RetryConfig:
    max_retries: int = 1
    timeout_ms: int = 5000
    backoff_ms: int = 500

class LLMClientWithRetry:
    def __init__(self, client: LLMClient, config: RetryConfig):
        self.client = client
        self.config = config

    async def generate_with_retry(
        self,
        request: LLMRequest
    ) -> tuple[Optional[LLMResponse], str]:
        """再試行付きで生成を実行"""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.generate(request)
                return response, None
            except TimeoutError as e:
                last_error = f"TIMEOUT_ERROR: {e}"
                await asyncio.sleep(self.config.backoff_ms / 1000)
            except Exception as e:
                last_error = f"LLM_ERROR: {e}"
                await asyncio.sleep(self.config.backoff_ms / 1000)

        return None, last_error
```

### フォールバック制御

```python
class LLMService:
    def __init__(
        self,
        primary_client: LLMClient,
        fallback_provider: FallbackProvider
    ):
        self.primary = LLMClientWithRetry(
            primary_client,
            RetryConfig(max_retries=1)
        )
        self.fallback = fallback_provider

    async def generate_axes(
        self,
        character: str
    ) -> tuple[list[Axis], str]:
        """評価軸を生成（フォールバック付き）"""
        request = LLMRequest(
            prompt=self._build_axes_prompt(character),
            model="gpt-4",
            temperature=0.7
        )

        response, error = await self.primary.generate_with_retry(request)

        if response is None:
            # フォールバックを使用
            logger.warning(f"Axes generation failed: {error}")
            return self.fallback.get_default_axes(), "FALLBACK_USED"

        # レスポンスをパース
        axes = self._parse_axes_response(response.content)

        # 軸数範囲外チェック
        if not (2 <= len(axes) <= 6):
            logger.warning(f"Invalid axis count: {len(axes)}")
            return self.fallback.get_default_axes(), "INVALID_AXIS_COUNT"

        return axes, None
```

## フォールバック資材

### 既定評価軸 (2軸)

```python
DEFAULT_AXES = [
    Axis(
        id="axis_default_1",
        name="論理性",
        description="論理的思考と感情的判断のバランス",
        direction="論理的 ⟷ 感情的"
    ),
    Axis(
        id="axis_default_2",
        name="社交性",
        description="集団行動と個人行動の指向性",
        direction="社交的 ⟷ 内省的"
    )
]
```

### 固定シナリオ (4シーン)

```python
FALLBACK_SCENARIOS = [
    Scene(
        number=1,
        scenario="あなたは新しいプロジェクトのリーダーに任命されました。"
                 "チームメンバーはまだ決まっていません。",
        choices=[
            Choice(
                id="fallback_1_1",
                text="すぐに計画書を作成する",
                weights={"axis_default_1": 0.8, "axis_default_2": -0.3}
            ),
            Choice(
                id="fallback_1_2",
                text="まず周囲に相談する",
                weights={"axis_default_1": -0.2, "axis_default_2": 0.7}
            ),
            Choice(
                id="fallback_1_3",
                text="過去の事例を調べる",
                weights={"axis_default_1": 0.5, "axis_default_2": -0.5}
            ),
            Choice(
                id="fallback_1_4",
                text="直感を信じて行動する",
                weights={"axis_default_1": -0.6, "axis_default_2": 0.2}
            )
        ]
    ),
    # scene 2-4 も同様に定義...
]
```

### プリセットタイプ (6種)

```python
PRESET_TYPES = [
    TypeResult(
        name="Balanced Mind",
        description="バランスの取れた判断を行う傾向があります。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Mid-Mid"
    ),
    TypeResult(
        name="Strategic",
        description="論理的で計画的な行動を好む傾向があります。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Hi-Lo"
    ),
    TypeResult(
        name="Empathetic",
        description="感情を重視し、他者との調和を大切にします。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Lo-Hi"
    ),
    TypeResult(
        name="Independent",
        description="独立心が強く、個人での活動を好みます。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Hi-Hi"
    ),
    TypeResult(
        name="Harmonizer",
        description="調和を重視し、柔軟な対応ができます。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Lo-Lo"
    ),
    TypeResult(
        name="Explorer",
        description="新しい経験を求め、積極的に行動します。",
        dominant_axes=["axis_default_1", "axis_default_2"],
        polarity="Mid-Hi"
    )
]
```

## エラーコード体系

### エラー分類
```python
class LLMErrorCode(Enum):
    # 再試行可能エラー
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"

    # 再試行不可エラー
    INVALID_REQUEST = "invalid_request"
    AUTHENTICATION_ERROR = "auth_error"
    QUOTA_EXCEEDED = "quota_exceeded"

    # フォールバック理由
    FALLBACK_USED = "fallback_used"
    INVALID_RESPONSE = "invalid_response"
    INVALID_AXIS_COUNT = "invalid_axis_count"
    INVALID_TYPE_COUNT = "invalid_type_count"
```

### ログ出力

```python
@dataclass
class LLMErrorLog:
    timestamp: datetime
    operation: str  # "axes", "scenario", "types"
    error_code: LLMErrorCode
    provider: LLMProvider
    latency_ms: float
    retry_count: int
    fallback_used: bool
    session_id: str

def log_llm_error(error_log: LLMErrorLog):
    """LLM エラーをログ出力"""
    logger.error(
        f"LLM Error: {error_log.operation}",
        extra={
            "error_code": error_log.error_code.value,
            "provider": error_log.provider.value,
            "latency_ms": error_log.latency_ms,
            "retry_count": error_log.retry_count,
            "fallback_used": error_log.fallback_used,
            "session_id": error_log.session_id
        }
    )
```

## フェイルオーバーフロー

### 評価軸生成
```
1. Primary LLM 呼び出し
   ↓ (失敗)
2. 1回リトライ
   ↓ (失敗)
3. 既定2軸を使用
   ↓
4. エラーログ出力 (FALLBACK_USED)
```

### シナリオ生成
```
1. Primary LLM 呼び出し
   ↓ (失敗)
2. 1回リトライ
   ↓ (失敗)
3. 固定シナリオを使用
   ↓
4. エラーログ出力 (FALLBACK_USED)
```

### タイプ生成
```
1. Primary LLM 呼び出し
   ↓ (失敗)
2. 1回リトライ
   ↓ (失敗)
3. プリセット6タイプから選択
   ↓
4. エラーログ出力 (FALLBACK_USED)
```

## 非機能要件

### パフォーマンス
- タイムアウト: 5秒
- バックオフ: 500ms
- 最大再試行: 1回

### 信頼性
- フェイルオーバー成功率: > 99%
- LLM 失敗検出率: 100% (エラーコード付与)

### コスト
- 推論コール数最小化
- 不要なリトライ抑制

## テストケース

### 正常系
- [x] LLM 呼び出しが成功する
- [x] レスポンスが正しくパースされる

### 異常系 - タイムアウト
- [x] タイムアウト時に1回リトライされる
- [x] 再試行失敗時にフォールバックが使用される
- [x] エラーログが出力される

### 異常系 - 軸数範囲外
- [x] 軸数が2未満の場合にフォールバック
- [x] 軸数が6超の場合にフォールバック

### 異常系 - 不正なレスポンス
- [x] JSON パースエラー時にフォールバック
- [x] 必須フィールド欠損時にフォールバック

### フォールバック
- [x] 既定評価軸が返される
- [x] 固定シナリオが返される
- [x] プリセットタイプが返される

## 実装優先度
1. LLM クライアント抽象化インタフェース
2. 再試行制御ロジック
3. タイムアウト制御
4. フォールバック資材準備
5. エラーコード体系定義
6. ログ出力実装
7. OpenAI/Anthropic 実装
8. モック実装 (開発・テスト用)

## 参考
- [要件定義](../requirements/overview.md) §14, §15.2
- [設計概要](./overview.md) §4, §6
- 関連 FR: FR-008, FR-011, FR-012, NFR-REL-001, NFR-REL-002

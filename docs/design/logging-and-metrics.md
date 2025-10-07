# ロギングとメトリクス整備設計

## 概要
NFR 要件を満たすためのロギングとメトリクス計測基盤の詳細設計。

関連 Issue: #8

## ロギング基盤

### ログレベル

```python
import logging
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

### ログ構造

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    session_id: str | None
    component: str  # "api", "llm", "scoring", etc.
    operation: str  # "session_start", "scene_gen", etc.
    latency_ms: float | None
    error_code: str | None
    metadata: dict
```

### ロガー設定

```python
import json
import sys

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"component": "%(name)s", "message": "%(message)s", '
        '"extra": %(extra)s}'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_logger("nightloom")
```

### ログ出力例

```python
def log_api_request(
    operation: str,
    session_id: str,
    latency_ms: float,
    status_code: int,
    error: str | None = None
):
    """API リクエストをログ出力"""
    logger.info(
        f"API Request: {operation}",
        extra={
            "session_id": session_id,
            "operation": operation,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "error": error
        }
    )

def log_llm_error(
    operation: str,
    session_id: str,
    error_code: str,
    provider: str,
    retry_count: int,
    fallback_used: bool
):
    """LLM エラーをログ出力"""
    logger.error(
        f"LLM Error: {operation}",
        extra={
            "session_id": session_id,
            "operation": operation,
            "error_code": error_code,
            "provider": provider,
            "retry_count": retry_count,
            "fallback_used": fallback_used
        }
    )
```

## メトリクス計測

### メトリクス定義

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Metric:
    name: str
    value: float
    unit: str
    tags: dict[str, str]
    timestamp: datetime
```

### メトリクスクライアント

```python
from abc import ABC, abstractmethod

class MetricsClient(ABC):
    @abstractmethod
    def record_latency(
        self,
        operation: str,
        latency_ms: float,
        tags: dict[str, str]
    ):
        """レイテンシを記録"""
        pass

    @abstractmethod
    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: dict[str, str] = None
    ):
        """カウンターをインクリメント"""
        pass

    @abstractmethod
    def record_gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] = None
    ):
        """ゲージ値を記録"""
        pass
```

### インメモリメトリクス実装 (MVP)

```python
from collections import defaultdict
from statistics import quantiles

class InMemoryMetrics(MetricsClient):
    def __init__(self):
        self.latencies: dict[str, List[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}

    def record_latency(
        self,
        operation: str,
        latency_ms: float,
        tags: dict[str, str] = None
    ):
        key = self._build_key(operation, tags)
        self.latencies[key].append(latency_ms)

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: dict[str, str] = None
    ):
        key = self._build_key(name, tags)
        self.counters[key] += value

    def record_gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] = None
    ):
        key = self._build_key(name, tags)
        self.gauges[key] = value

    def get_p95(self, operation: str) -> float:
        """p95 レイテンシを取得"""
        if operation not in self.latencies:
            return 0.0
        values = self.latencies[operation]
        if len(values) == 0:
            return 0.0
        return quantiles(values, n=20)[18]  # 95th percentile

    def _build_key(self, name: str, tags: dict[str, str] = None) -> str:
        if tags is None:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
```

## 計測ポイント

### API レイテンシ計測

```python
from functools import wraps
import time

def measure_latency(operation: str):
    """API レイテンシを計測するデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000

                metrics.record_latency(
                    operation,
                    latency_ms,
                    tags={"status": "success"}
                )

                log_api_request(
                    operation=operation,
                    session_id=kwargs.get("session_id", "unknown"),
                    latency_ms=latency_ms,
                    status_code=200
                )

                return result
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000

                metrics.record_latency(
                    operation,
                    latency_ms,
                    tags={"status": "error"}
                )

                log_api_request(
                    operation=operation,
                    session_id=kwargs.get("session_id", "unknown"),
                    latency_ms=latency_ms,
                    status_code=500,
                    error=str(e)
                )

                raise

        return wrapper
    return decorator

# 使用例
@measure_latency("session_start")
async def start_session():
    # ...
    pass
```

### LLM 呼び出し計測

```python
async def generate_with_metrics(
    client: LLMClient,
    request: LLMRequest,
    operation: str
) -> LLMResponse:
    """LLM 呼び出しとメトリクス計測"""
    start_time = time.time()

    try:
        response = await client.generate(request)
        latency_ms = (time.time() - start_time) * 1000

        # メトリクス記録
        metrics.record_latency(
            f"llm_{operation}",
            latency_ms,
            tags={"provider": response.provider.value, "status": "success"}
        )

        # トークン使用量記録
        metrics.increment_counter(
            "llm_tokens_used",
            value=response.tokens_used,
            tags={"provider": response.provider.value}
        )

        return response

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        metrics.record_latency(
            f"llm_{operation}",
            latency_ms,
            tags={"provider": request.model, "status": "error"}
        )

        metrics.increment_counter(
            "llm_errors",
            tags={"operation": operation, "error_type": type(e).__name__}
        )

        raise
```

### フェイルオーバー計測

```python
def record_failover(
    operation: str,
    session_id: str,
    reason: str,
    fallback_used: bool
):
    """フェイルオーバー発生を記録"""
    metrics.increment_counter(
        "failover_total",
        tags={
            "operation": operation,
            "reason": reason,
            "fallback_used": str(fallback_used)
        }
    )

    log_llm_error(
        operation=operation,
        session_id=session_id,
        error_code=reason,
        provider="unknown",
        retry_count=1,
        fallback_used=fallback_used
    )
```

## NFR 要件対応

### NFR-PERF: パフォーマンス計測

```python
class PerformanceMonitor:
    def __init__(self, metrics: MetricsClient):
        self.metrics = metrics

    def check_performance_targets(self) -> dict[str, bool]:
        """パフォーマンス目標達成状況をチェック"""
        return {
            "scene_gen_p95": self.metrics.get_p95("scene_gen") <= 800,
            "result_gen_p95": self.metrics.get_p95("result_gen") <= 1200,
            "full_session_p95": self.metrics.get_p95("full_session") <= 4500
        }
```

### NFR-REL: 信頼性計測

```python
class ReliabilityMonitor:
    def __init__(self, metrics: MetricsClient):
        self.metrics = metrics

    def calculate_failover_rate(self) -> float:
        """フェイルオーバー成功率を計算"""
        total = self.metrics.counters.get("failover_total", 0)
        success = self.metrics.counters.get(
            "failover_total[fallback_used=True]", 0
        )

        if total == 0:
            return 1.0

        return success / total

    def calculate_llm_error_detection_rate(self) -> float:
        """LLM エラー検出率を計算"""
        errors = self.metrics.counters.get("llm_errors", 0)
        errors_with_code = self.metrics.counters.get(
            "llm_errors_with_code", 0
        )

        if errors == 0:
            return 1.0

        return errors_with_code / errors
```

## メトリクス可視化エンドポイント

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """メトリクスサマリーを取得"""
    return {
        "latencies": {
            "scene_gen_p95": metrics.get_p95("scene_gen"),
            "result_gen_p95": metrics.get_p95("result_gen"),
            "full_session_p95": metrics.get_p95("full_session")
        },
        "counters": {
            "sessions_total": metrics.counters.get("sessions_total", 0),
            "llm_errors": metrics.counters.get("llm_errors", 0),
            "failover_total": metrics.counters.get("failover_total", 0)
        },
        "performance_targets": PerformanceMonitor(metrics).check_performance_targets(),
        "reliability": {
            "failover_rate": ReliabilityMonitor(metrics).calculate_failover_rate()
        }
    }
```

## PII 非含ポリシー

### 禁止事項
- ユーザー IP アドレス
- ユーザーエージェント詳細
- キーワード内容の詳細ログ (ハッシュ化は可)
- 選択肢テキストの詳細ログ

### 許可事項
- セッション ID (推測困難な UUID)
- タイムスタンプ
- レイテンシ
- エラーコード
- カウンター

## 実装優先度
1. ロガー基盤設定
2. エラーログ出力実装
3. API レイテンシ計測
4. LLM 呼び出し計測
5. フェイルオーバー記録
6. メトリクス可視化エンドポイント
7. (将来) 外部メトリクスサービス連携

## 参考
- [要件定義](../requirements/overview.md) §15, §16
- [設計概要](./overview.md) §5.2
- 関連 FR: FR-017, FR-024, NFR-PERF-001〜004, NFR-REL-001〜002, NFR-SEC-001

# Research: NightLoom外部LLMサービス統合

**Branch**: `004-nightloom-llm-openai` | **Date**: 2025-10-20 | **Spec**: [spec.md](spec.md)

## 研究概要

NightLoomの外部LLMサービス統合に向けて、OpenAI/Anthropic APIの技術仕様、プロンプトエンジニアリング手法、コスト・パフォーマンス最適化、統合アーキテクチャを調査した。

## 1. OpenAI API統合技術

### 決定: OpenAI Python SDK + gpt-4-turbo使用

**根拠**:
- 公式SDKによる型安全性とエラーハンドリング
- gpt-4-turboの高い推論品質と相対的低コスト
- 豊富なドキュメントと実用例

**検討した代替案**:
- 直接HTTP API呼び出し → SDK採用でエラーハンドリング複雑性回避
- gpt-3.5-turbo → 診断品質要件からgpt-4選択
- Azure OpenAI → 初期はOpenAI直接利用、将来的に企業展開時検討

**実装詳細**:
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = await client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=1000,
    timeout=5.0
)
```

## 2. Anthropic Claude統合技術

### 決定: Anthropic Python SDK + claude-3-sonnet使用

**根拠**:
- OpenAIとの価格・性能バランス比較で選択肢提供
- 異なるLLMによる出力品質の多様性確保
- プロバイダー障害時の冗長性

**検討した代替案**:
- claude-3-opus → コスト要件（0.05USD/セッション）から見送り
- HTTP直接統合 → SDK採用でメンテナンス性向上

**実装詳細**:
```python
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    temperature=0.7,
    messages=[{"role": "user", "content": prompt}],
    timeout=5.0
)
```

## 3. プロンプトテンプレート設計

### 決定: Jinja2テンプレートシステム採用

**根拠**:
- 変数展開・条件分岐による柔軟なプロンプト生成
- 外部ファイル管理による実装後の調整容易性
- Pythonエコシステムでの標準的選択

**テンプレート例**:
```jinja2
# templates/prompts/keyword_generation.j2
あなたは日本語の性格診断システムの専門家です。

初期文字「{{ initial_character }}」から始まる、性格診断に適したキーワード候補を4つ生成してください。

要件:
- 各キーワードは2-8文字の日本語
- 性格的な価値観や行動指針を表現
- バラエティに富んだ概念的多様性

出力形式:
```json
{
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4"]
}
```
```

**検討した代替案**:
- ハードコード化 → 調整困難、A/Bテスト不可から却下
- f-string テンプレート → 複雑性でJinja2採用
- 外部設定API → 過度な複雑性から見送り

## 4. コスト最適化戦略

### 決定: トークン数制限 + キャッシュ戦略

**分析結果**:
- GPT-4-turbo: $0.01/1K入力トークン、$0.03/1K出力トークン
- Claude-3-sonnet: $0.003/1K入力トークン、$0.015/1K出力トークン
- 目標: 0.05USD/セッション以内

**最適化手法**:
1. **プロンプト簡潔化**: 必要最小限の指示文
2. **出力制限**: max_tokens=1000で生成量制御
3. **バッチ処理**: 複数軸を一回で生成（シーン生成時）
4. **フォールバック活用**: レート制限95%で早期切り替え

**検討した代替案**:
- レスポンスキャッシュ → セッション独立性要件と矛盾
- より安価なモデル → 品質要件満たさず

## 5. エラーハンドリング・フォールバック戦略

### 決定: 段階的フォールバック + 即座復旧

**戦略**:
1. **1回リトライ**: ネットワーク一時障害対応
2. **5秒タイムアウト**: レスポンス性要件維持
3. **フォールバック資産**: 既存静的データで継続性保証
4. **プロバイダー切り替え**: OpenAI障害時Anthropic自動切り替え

**実装パターン**:
```python
async def generate_with_fallback(prompt_template, **kwargs):
    try:
        result = await primary_llm.generate(prompt_template, **kwargs)
        return result, False  # fallback_used=False
    except (TimeoutError, RateLimitError, APIError):
        try:
            result = await secondary_llm.generate(prompt_template, **kwargs)
            return result, False
        except Exception:
            result = get_fallback_content(kwargs.get('content_type'))
            return result, True  # fallback_used=True
```

## 6. パフォーマンス・監視戦略

### 決定: 非同期処理 + メトリクス埋め込み

**パフォーマンス要件**:
- LLM API呼び出し: p95 < 5s
- 全診断完了時間: p95 < 8s (既存4.5s + LLM処理時間)

**監視項目**:
- API応答時間分布（プロバイダー別）
- フォールバック発動率
- 使用トークン数・コスト追跡
- 生成品質（形式検証通過率）

**実装手法**:
```python
@observe_llm_call
async def generate_bootstrap_data(self, initial_character: str):
    start_time = time.time()
    try:
        result = await self._call_llm(template, character=initial_character)
        self.metrics.record_success(time.time() - start_time)
        return result
    except Exception as e:
        self.metrics.record_failure(str(e))
        raise
```

## 7. 設定管理・デプロイ戦略

### 決定: 環境変数 + 設定バリデーション

**設定項目**:
```bash
# プロバイダー選択
LLM_PROVIDER=openai  # openai/anthropic/mock

# API認証
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# パフォーマンス調整
LLM_TIMEOUT=5.0
LLM_MAX_RETRIES=1
LLM_RATE_LIMIT_THRESHOLD=0.95
```

**バリデーション**:
- 起動時設定チェック
- APIキー有効性確認
- フォールバック資産整合性検証

## 8. テスト戦略

### 決定: 階層化テスト + モック/実統合

**テスト層**:
1. **Unit Tests**: プロンプト生成、設定管理、エラーハンドリング
2. **Integration Tests**: 実API呼び出し（テスト用APIキー）
3. **E2E Tests**: フォールバック動作、セッション完全性

**モック戦略**:
```python
# テスト用モック
class MockLLMClient:
    async def generate(self, prompt, **kwargs):
        # 決定的な出力でテスト予測性確保
        return predefined_responses[kwargs.get('content_type')]
```

## 研究結論

外部LLMサービス統合に必要な技術要素を特定し、実装方針を確定した。OpenAI/Anthropic両プロバイダー対応、Jinja2テンプレートシステム、段階的フォールバック戦略により、堅牢で柔軟性の高いAI統合を実現する。コスト0.05USD/セッション以内、パフォーマンスp95 8秒以内の要件を満たす設計が整った。

次のPhase 1では、データモデル設計とAPI契約仕様を具体化する。

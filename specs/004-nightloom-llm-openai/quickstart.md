# Quickstart: NightLoom外部LLMサービス統合

**Branch**: `004-nightloom-llm-openai` | **Date**: 2025-10-20 | **Spec**: [spec.md](spec.md)

## 開発環境セットアップ

### 1. 前提条件

- Python 3.12以上
- Node.js 20 LTS以上
- 既存のNightLoomプロジェクト環境

### 2. 依存関係インストール

#### Backend
```bash
cd backend

# OpenAI SDK追加
uv add openai

# Anthropic SDK追加  
uv add anthropic

# Jinja2テンプレートエンジン追加
uv add jinja2

# 開発依存関係同期
uv sync --extra dev
```

#### Frontend
```bash
# フロントエンドは既存APIとの互換性維持により変更なし
cd frontend
pnpm install
```

### 3. 環境変数設定

`.env` ファイルを作成：

```bash
# LLMプロバイダー設定
LLM_PROVIDER=openai  # openai/anthropic/mock

# API キー（本番環境では適切に管理）
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# パフォーマンス設定
LLM_TIMEOUT=5.0
LLM_MAX_RETRIES=1
LLM_RATE_LIMIT_THRESHOLD=0.95
LLM_COST_LIMIT_PER_SESSION=0.05
```

### 4. プロンプトテンプレート準備

```bash
# テンプレートディレクトリ作成
mkdir -p backend/app/templates/prompts

# 基本テンプレートファイル作成（実装時に詳細化）
touch backend/app/templates/prompts/keyword_generation.j2
touch backend/app/templates/prompts/axis_creation.j2  
touch backend/app/templates/prompts/scenario_generation.j2
touch backend/app/templates/prompts/result_analysis.j2
```

## 開発サーバー起動

### Backend（LLM統合機能付き）
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend（既存）
```bash
cd frontend  
pnpm dev
```

### サービス確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# LLMプロバイダー状態確認
curl http://localhost:8000/api/llm/providers

# 既存セッション作成（互換性確認）
curl -X POST http://localhost:8000/api/sessions/start
```

## 実装手順（優先度順）

### Phase 1: LLM基盤実装（P1）
1. **LLMProvider設定システム**
   ```bash
   # 実装対象ファイル
   backend/app/config/llm_config.py
   backend/app/clients/llm_providers.py
   ```

2. **OpenAI統合**
   ```bash
   backend/app/clients/openai_client.py
   backend/tests/unit/test_openai_client.py
   ```

3. **フォールバック機能**
   ```bash
   # 既存フォールバック資産拡張
   backend/app/services/fallback_assets.py
   ```

### Phase 2: プロンプト管理（P2）
1. **テンプレート管理システム**
   ```bash
   backend/app/services/prompt_manager.py
   backend/tests/unit/test_prompt_manager.py
   ```

2. **基本プロンプト作成**
   ```bash
   backend/app/templates/prompts/
   ```

### Phase 3: 統合・監視（P3）
1. **セッションサービス拡張**
   ```bash
   # 既存サービス拡張
   backend/app/services/session.py
   ```

2. **使用量監視**
   ```bash
   backend/app/services/usage_monitor.py
   backend/tests/integration/test_usage_monitoring.py
   ```

### Phase 4: Anthropic統合（P4）
1. **Claude統合**
   ```bash
   backend/app/clients/anthropic_client.py
   backend/tests/unit/test_anthropic_client.py
   ```

## テスト戦略

### Unit Tests
```bash
# LLMクライアントテスト
cd backend
uv run pytest tests/unit/test_*_client.py -v

# プロンプト管理テスト
uv run pytest tests/unit/test_prompt_manager.py -v

# 設定管理テスト
uv run pytest tests/unit/test_llm_config.py -v
```

### Integration Tests
```bash
# LLM統合テスト（実API使用・テストキー必要）
uv run pytest tests/integration/test_llm_integration.py -v

# セッション統合テスト
uv run pytest tests/integration/test_session_llm.py -v
```

### E2E Tests
```bash
# フロントエンド統合テスト
cd frontend
pnpm test:e2e:llm
```

## パフォーマンス測定

### API応答時間測定
```bash
# LLM応答時間測定スクリプト
cd backend
uv run python scripts/measure_llm_performance.py
```

### コスト追跡
```bash
# 使用量・コスト確認
curl http://localhost:8000/api/llm/usage/stats?date=2025-10-20
```

## デバッグ・トラブルシューティング

### ログ確認
```bash
# LLM関連ログ
tail -f logs/llm_service.log

# パフォーマンスログ  
tail -f logs/performance.log
```

### よくある問題

#### OpenAI API Key エラー
```bash
# APIキー確認
echo $OPENAI_API_KEY

# 権限テスト
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### レート制限エラー
```bash
# 使用量確認
curl http://localhost:8000/api/llm/providers/openai/health

# フォールバック動作確認
curl -X POST http://localhost:8000/api/llm/generate/keywords \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","initial_character":"あ"}'
```

#### パフォーマンス問題
```bash
# 応答時間分析
curl -w "@curl-format.txt" -s -o /dev/null \
  http://localhost:8000/api/llm/providers

# メモリ使用量確認
ps aux | grep uvicorn
```

## プロダクション準備

### 設定チェックリスト
- [ ] 環境変数適切設定
- [ ] APIキー権限確認
- [ ] プロンプトテンプレート最適化
- [ ] フォールバック動作確認
- [ ] パフォーマンス要件達成
- [ ] コスト制限設定
- [ ] 監視・アラート設定

### セキュリティチェック
- [ ] APIキー適切管理（環境変数・暗号化）
- [ ] LLM応答内容検証
- [ ] レート制限適切設定
- [ ] ログ機密情報マスキング

### 監視設定
- [ ] API応答時間監視
- [ ] エラー率監視
- [ ] コスト使用量監視
- [ ] フォールバック発動率監視

## 参考資料

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/)

## 次のステップ

1. `/speckit.tasks` でタスク分解実行
2. P1 LLM基盤実装から開始
3. プロンプトエンジニアリングによる品質向上
4. パフォーマンス最適化とコスト監視
5. 本番運用へのデプロイ

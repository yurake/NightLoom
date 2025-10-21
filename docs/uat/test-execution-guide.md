# NightLoom 生成AI機能 UAT総合テスト実行手順書

---

## 1. テストレベル別 実行手順

### 1.1 クイック確認（約1分）
- [`docs/uat/quick-llm-check.md`](docs/uat/quick-llm-check.md) の手順に従い、環境変数・APIキー・サーバー起動・API/画面動作を確認
- 主要コマンド例:
  ```bash
  echo $OPENAI_API_KEY
  echo $ANTHROPIC_API_KEY
  curl -s http://localhost:8000/health
  curl -X POST http://localhost:8000/api/sessions/start -H "Content-Type: application/json" -d '{"initial_character": "あ"}' | jq
  ```
- 判定ポイント: 正常レスポンス、fallbackUsedフラグ、画面表示

### 1.2 基本統合テスト（約5分）
- バックエンド・フロントエンドのテストファイル群を実行
- 主要コマンド例:
  ```bash
  # バックエンド
  cd backend && uv sync && uv run --extra dev pytest -v

  # フロントエンド
  pnpm --filter nightloom-frontend test

  # E2Eテスト
  pnpm --filter nightloom-frontend test:e2e
  ```
- 判定ポイント: 全テストパス、エラーなし

### 1.3 詳細UATケース（約15分）
- [`docs/uat/nightloom-llm-uat-cases.md`](docs/uat/nightloom-llm-uat-cases.md) の全シナリオを網羅的に実施
- 境界値・異常系・統合・フォールバック・セッション管理まで確認
- 必要に応じてAPI直接呼び出し・画面操作・ログ確認

---

## 2. 実行環境別 手順

### 2.1 開発環境
- 上記コマンドをローカルで実行
- サーバー起動:  
  - バックエンド: `cd backend && uv run uvicorn app.main:app --reload`
  - フロントエンド: `pnpm --filter nightloom-frontend dev`

### 2.2 CI/CD環境（GitHub Actions）
- `.github/workflows/ci.yml` により自動テスト実行
  - バックエンド: `uv run --extra dev pytest -v`
  - フロントエンド: `pnpm test`
  - E2E: `pnpm test:e2e`
- Playwrightレポート自動アップロード（失敗時）

### 2.3 本番環境
- 本番ビルド後、主要API/画面の動作確認
- 必要に応じてクイック確認手順を実施

---

## 3. テスト実行コマンド集

### バックエンド
- `uv run --extra dev pytest -v`

### フロントエンド
- `pnpm --filter nightloom-frontend test`

### E2Eテスト
- `pnpm --filter nightloom-frontend test:e2e`

---

## 4. 結果確認・判定基準

### 成功基準
- 全テストパス（エラー・警告なし）
- API/画面が正常応答
- fallbackUsed: false（LLM正常時）、true（フォールバック時も機能継続）
- レスポンス時間: 2-5秒以内（通常）

### 失敗時の対処
- エラーログ・テストレポートを確認
- 環境変数・APIキー・依存関係・サーバー起動状態を再確認
- 必要に応じて再実行・修正

### レポート出力方法
- pytest/Jest/Playwrightの標準レポート
- CI/CD失敗時はPlaywrightレポートが自動アップロード（`frontend/playwright-report/`）

---

## 5. トラブルシューティング

### よくある問題と解決方法
- fallbackUsed: trueが常に表示 → APIキー・クォータ・環境変数確認
- シーンが表示されない → セッションID・コンソールエラー確認
- キーワードが初期文字で始まらない → プロンプト・レスポンスパース確認

### 環境設定のトラブル対応
- Python/Node.jsバージョン不一致 → `.python-version`・`.nvmrc`参照
- 依存関係エラー → `uv sync`・`pnpm install`再実行

---

## 付録：テストファイル一覧

- バックエンド: [`backend/tests/`](backend/tests/)
- フロントエンド: [`frontend/tests/`](frontend/tests/)
- E2E: [`frontend/e2e/`](frontend/e2e/)

---

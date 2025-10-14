# Quickstart - NightLoom MVP診断体験

このドキュメントは NightLoom MVP の開発環境を最短で立ち上げる手順をまとめたものです。詳細はリポジトリの `README.md` や `docs/` を参照してください。

---

## 1. 前提ツール

- Python 3.12
- Node.js 20.x（nvm 利用推奨）
- pnpm 9+
- uv（Python パッケージ管理）
- Playwright 依存ブラウザ（`pnpm exec playwright install`）

---

## 2. リポジトリ初期化

```bash
git clone https://github.com/yurake/NightLoom.git
cd NightLoom
```

作業ブランチ（例: `001-initial-plan`）をチェックアウトしておく。

---

## 3. バックエンドセットアップ (FastAPI)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### バックエンドテスト

```bash
uv run --extra dev pytest
```

Play 状態のセッションを CLI から確認する場合は `uv run python -m app.scripts.seed_preview` 等（将来実装予定）。

---

## 4. フロントエンドセットアップ (Next.js 14)

```bash
cd ..
pnpm install --filter nightloom-frontend
pnpm --filter nightloom-frontend dev
```

ブラウザで http://localhost:3000 を開き、初期プロンプト→シーン進行→結果表示のフローを確認する。

### フロントエンドテスト

```bash
pnpm --filter nightloom-frontend test          # ユニットテスト
pnpm --filter nightloom-frontend test:e2e      # Playwright E2E
```

E2E 実行前に `pnpm exec playwright install` を実行して依存ブラウザを準備する。

---

## 5. 監視・メトリクスの確認

- バックエンド: ログに `request_latency_ms`, `fallback_used`, `session_state` などが出力される。ローカルではコンソールで確認。
- フロントエンド: ブラウザ DevTools の Performance タブで結果画面アニメーション（1s以内）を計測する。

---

## 6. 開発フロー

1. `specs/001-initial-plan/spec.md` と `clarification-results.md` を参照して要件を確認。
2. `plan.md` に従い Phase 1/Phase 2 のタスクを消化。
3. 実装後はユニット・統合・E2E テストを実行し、フォールバックシナリオを手動検証。
4. 変更内容を PR にまとめ、品質チェックリストで網羅性を確認。

---

## 7. トラブルシューティング

- **LLM 応答が停止する**: バックエンドログで `fallback_reason` を確認し、固定資材が適用されているか検証。
- **結果画面が白紙**: API `/api/sessions/{id}/result` のレスポンスを確認し、`typeProfiles` が4〜6件存在するかをチェック。
- **Playwright テストが失敗**: `pnpm test:e2e --debug` を利用し、遅延を許容するためのタイムアウト調整を検討。

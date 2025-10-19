# Quickstart - NightLoom MVP診断体験

このドキュメントは NightLoom MVP の開発環境を最短で立ち上げる手順をまとめたものです。Phase 6 Polish完了版に対応しています。

---

## 1. 前提ツール

**必須**
- Python 3.12
- Node.js 20.x（`.nvmrc`で管理、nvm利用推奨）
- pnpm 9+
- uv（Python パッケージ管理）

**テスト実行時**
- Playwright 依存ブラウザ（`pnpm exec playwright install`）

---

## 2. 環境セットアップ

### リポジトリクローン
```bash
git clone <repository-url>
cd NightLoom

# Node.js バージョン設定（nvm使用時）
nvm use
```

### 依存関係一括インストール
```bash
# ワークスペース全体の依存関係をインストール
pnpm install
```

---

## 3. 開発サーバー起動

### バックエンド（ターミナル1）
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**サーバー確認**: http://localhost:8000/health で `{"status": "ok"}` が返ることを確認

### フロントエンド（ターミナル2）
```bash
# プロジェクトルートから実行
pnpm --filter nightloom-frontend dev
```

**アプリ確認**: http://localhost:3000 で NightLoom 診断体験が利用可能

---

## 4. テスト実行

### 全テスト実行
```bash
# バックエンド
cd backend && uv run --extra dev pytest -v

# フロントエンド（プロジェクトルートから）
pnpm --filter nightloom-frontend test              # ユニットテスト
pnpm --filter nightloom-frontend test:e2e          # E2E テスト
pnpm --filter nightloom-frontend lint              # ESLint
```

### アクセシビリティテスト
```bash
# axe-core による自動テスト
pnpm --filter nightloom-frontend test -- --testNamePattern="accessibility"

# E2E アクセシビリティテスト
pnpm --filter nightloom-frontend test:e2e -- accessibility-keyboard.spec.ts
```

---

## 5. 品質・パフォーマンス確認

### パフォーマンス監視
- **Web Vitals**: ブラウザ DevTools > Console でメトリクス確認
- **API レスポンス**: Network タブで `/api/sessions/*` の応答時間確認
- **セキュリティ**: http://localhost:8000/security-stats で統計確認

### アクセシビリティ検証
- **キーボード操作**: Tab、Enter、Escapeキーでの完全操作
- **スクリーンリーダー**: NVDA/VoiceOver での読み上げ確認
- **カラーコントラスト**: WCAG AA 準拠（4.5:1 以上）

### セキュリティ検証
- **レート制限**: 短時間での連続リクエストで429エラー発生確認
- **入力検証**: 無効な文字列での400エラー確認
- **セッション保護**: 不正なセッションIDでの適切なエラーレスポンス

---

## 6. 本格運用準備

### プロダクションビルド
```bash
# フロントエンド最適化ビルド
pnpm --filter nightloom-frontend build

# バックエンド依存関係最適化
cd backend && uv sync --frozen
```

### 環境変数設定
```bash
# .env.local (フロントエンド)
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.nightloom.app

# .env (バックエンド) 
ENVIRONMENT=production
ALLOWED_ORIGINS=https://nightloom.app,https://www.nightloom.app
```

---

## 7. トラブルシューティング

### 開発環境
- **ポート衝突**: バックエンド8000番、フロントエンド3000番の空き確認
- **依存関係エラー**: `pnpm install` と `uv sync` の再実行
- **テスト失敗**: `pnpm exec playwright install` でブラウザ再インストール

### パフォーマンス問題
- **応答遅延**: `/security-stats` でレート制限状況確認
- **メモリ使用量**: 長時間運用時のセッションデータクリーンアップ
- **フロントエンド遅延**: DevTools Performance タブでボトルネック特定

### セキュリティ問題
- **異常アクセス**: ログで `rate_limit` イベント確認
- **入力検証エラー**: `VALIDATION_ERROR` レスポンスの詳細確認
- **CORS エラー**: `main.py` の `allow_origins` 設定確認

---

## 8. 開発フロー（Phase 6 対応）

### 品質ゲート
1. **型チェック**: `tsc --noEmit` エラー0
2. **リント**: `eslint` エラー0  
3. **テスト**: 全テスト通過
4. **アクセシビリティ**: axe-core エラー0
5. **パフォーマンス**: Core Web Vitals "Good"

### コード変更時の確認項目
- [ ] 既存テストの通過
- [ ] 新機能のテスト追加
- [ ] アクセシビリティへの影響確認
- [ ] モバイル表示の確認
- [ ] パフォーマンス影響の測定
- [ ] セキュリティ影響の評価

---

**Phase 6 Polish Status**: Production Ready ✅
**品質保証**: WCAG 2.1 AA準拠、90%+テストカバレッジ、セキュリティ強化済み

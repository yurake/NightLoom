# NightLoom

NightLoom は、分岐型の短編シナリオ体験を通じてユーザーの意思決定傾向を観測し、AI が動的に評価軸とタイプ分類を生成する Web アプリケーションです。MVP では 4 シーン構成の診断フローと高速なフェイルオーバーを備えた SPA を目標に開発を進めています。

## MVP のコア機能
- 4 シーン × 各 4 選択肢で構成される単一セッション診断
- LLM による評価軸（2〜6 軸）とタイプ分類の動的生成
- 選択結果の正規化スコア計算とタイプ判定のリアルタイム表示
- LLM 応答失敗時のプリセットシナリオ・タイプによるフェイルオーバー
- ブラウザ（PC/モバイル）対応のシングルページアプリケーション

詳細要件は `docs/requirements/overview.md` を参照してください。

## リポジトリ構成
```text
.
├── backend/            # FastAPI バックエンド（uv/uvicorn ベース）
├── frontend/           # Next.js 14 + Tailwind CSS のフロントエンド
├── docs/               # 要件・設計・運用ドキュメント
├── CONTRIBUTING.md     # 開発フローとコーディング規約
├── AGENTS.md           # エージェント向けガイドライン
├── pnpm-workspace.yaml # フロントエンドのワークスペース設定
└── README.md
```

## 技術スタック
| 領域 | 採用技術 |
| --- | --- |
| バックエンド | Python 3.12, FastAPI, Uvicorn, uv |
| フロントエンド | Next.js 14, React 18, TypeScript, Tailwind CSS |
| テスト | pytest, httpx, Jest, Testing Library, Playwright |
| パッケージ管理 | uv（Python）, pnpm（Node.js） |

## セットアップ
### 前提ツール
- Python 3.12 系
- Node.js 20 系
- uv（https://github.com/astral-sh/uv）
- pnpm 9 以降

追加ツールや運用ルールは `CONTRIBUTING.md` を参照してください。

### バックエンド
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

開発用テスト:
```bash
uv run --extra dev pytest
```

### フロントエンド
```bash
pnpm install
pnpm --filter frontend dev
```

ユニットテスト:
```bash
pnpm --filter frontend test
```

E2E テスト:
```bash
pnpm --filter frontend test:e2e
```

## ドキュメントと開発フロー
- プロジェクト運用ルール: `CONTRIBUTING.md`
- ドキュメントガイド: `docs/README.md`
- 要件と設計: `docs/requirements/overview.md`, `docs/design/overview.md`
- ロードマップとタスク管理: `docs/roadmap/overview.md`, `docs/todo/`

作業内容や検討事項は `docs/` 配下に追記し、ToDo 進行状況は `docs/todo/` の運用ルールに従って更新してください。

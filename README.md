# NightLoom

NightLoom は、分岐型の短編シナリオ体験を通じてユーザーの意思決定傾向を観測し、AI が動的に評価軸とタイプ分類を生成する Web アプリケーションです。MVP では 4 シーン構成の診断フローと高速なフェイルオーバーを備えた SPA を目標に開発を進めています。

## 実装状況
### 完了機能 ✅
- **結果画面表示機能**: TypeCard、AxisScoreItem、AxesScores、ResultScreen コンポーネントの実装完了
- **TypeScript型定義**: 診断結果・評価軸・タイプ分類の型システム構築
- **テストカバレッジ**: 43テストケース実装済み（Jest + Testing Library + Playwright）
- **テーマシステム**: 複数テーマ対応とダイナミック切り替え機能
- **API クライアント**: セッション管理・エラーハンドリング実装

### 開発中機能 🚧
- バックエンドAPI実装（FastAPI基盤構築済み）
- LLM クライアント統合
- 診断フロー実装

## MVP のコア機能
- 4 シーン × 各 4 選択肢で構成される単一セッション診断
- LLM による評価軸（2〜6 軸）とタイプ分類の動的生成
- 選択結果の正規化スコア計算とタイプ判定のリアルタイム表示
- LLM 応答失敗時のプリセットシナリオ・タイプによるフェイルオーバー
- ブラウザ（PC/モバイル）対応のシングルページアプリケーション

## プロジェクト構成
```text
NightLoom/
├── .github/workflows/  # CI/CD設定（GitHub Actions）
├── backend/            # FastAPI バックエンド（Python 3.12 + uv）
│   ├── app/           # アプリケーションコード
│   └── tests/         # バックエンドテスト
├── frontend/          # Next.js 14 フロントエンド
│   ├── app/           # App Routerアプリケーション
│   ├── tests/         # Jestユニットテスト
│   └── e2e/           # Playwright E2Eテスト
├── docs/              # プロジェクトドキュメント
├── specs/             # 要件・設計仕様書
├── pnpm-workspace.yaml # pnpmワークスペース設定
└── README.md          # このファイル
```

## 技術スタック
| 領域 | 採用技術 |
| --- | --- |
| バックエンド | Python 3.12, FastAPI, Uvicorn, uv |
| フロントエンド | Next.js 14, React 18, TypeScript 5.5, Tailwind CSS 3.4 |
| テスト | pytest + httpx（Backend）, Jest + Testing Library + Playwright（Frontend） |
| リンター・フォーマッター | ESLint 9.9（Frontend）, Next.js ESLint Config |
| パッケージ管理 | uv（Python）, pnpm 9+（Node.js Workspace） |
| 開発環境 | GitHub Actions CI, Node.js 20 LTS |

## 開発環境セットアップ

### 前提ツール
- **Python 3.12 系** - バックエンド開発
- **Node.js 20 LTS** - フロントエンド開発（`.nvmrc`で管理）
- **uv** - Python依存関係管理（https://github.com/astral-sh/uv）
- **pnpm 9+** - Node.js Workspace管理
- **nvm** (推奨) - Node.jsバージョン管理

### クイックスタート
```bash
# リポジトリルートで実行
git clone <repository-url>
cd NightLoom

# Node.js環境設定（nvm使用時）
nvm use

# 依存関係インストール
pnpm install

# バックエンド起動
cd backend && uv sync && uv run uvicorn app.main:app --reload

# フロントエンド起動（別ターミナル）
pnpm --filter nightloom-frontend dev
```

### 詳細な起動手順

#### バックエンド開発サーバー
```bash
cd backend
uv sync                                    # 依存関係同期
uv run uvicorn app.main:app --reload      # 開発サーバー起動
```

**テスト実行:**
```bash
uv run --extra dev pytest                 # 全テスト実行
uv run --extra dev pytest -v              # バーボーズ出力
```

#### フロントエンド開発サーバー
```bash
# Node.js環境確認・設定
nvm use                                    # .nvmrcに基づく設定

# pnpm workspace経由での操作
pnpm install --filter nightloom-frontend  # 依存関係インストール
pnpm --filter nightloom-frontend dev      # 開発サーバー起動
pnpm --filter nightloom-frontend build    # プロダクションビルド
```

**テスト実行:**
```bash
pnpm --filter nightloom-frontend test              # Jestユニットテスト
pnpm --filter nightloom-frontend test:e2e          # Playwright E2Eテスト
pnpm --filter nightloom-frontend lint              # ESLint実行
```

**注意事項:**
- 開発サーバー終了時は `Ctrl+C` で明示的に停止してください
- CI環境では GitHub Actions で自動テスト実行されます

## 開発・運用情報

### アーキテクチャ概要
- **フロントエンド**: Next.js 14 App Router + TypeScript
- **バックエンド**: FastAPI + Python 3.12
- **デプロイ**: SPA形式でのスタティック配信予定
- **API通信**: RESTful API（JSON）
- **状態管理**: React Server Components + Client Components

### テスト戦略
| テスト種別 | 対象 | ツール | 実行タイミング |
|------------|------|--------|----------------|
| ユニットテスト | React コンポーネント | Jest + Testing Library | 開発時・CI |
| E2Eテスト | ユーザーフロー | Playwright | 開発時・CI |
| バックエンドテスト | API・ビジネスロジック | pytest | 開発時・CI |
| 型チェック | TypeScript | tsc | 開発時・CI |
| リンター | コード品質 | ESLint | 開発時・CI |

### CI/CD設定
GitHub Actions による自動化：
- **バックエンド**: Python依存関係インストール、pytestテスト実行
- **フロントエンド**: Node.js環境セットアップ、依存関係インストール、型チェック、ESLint、Jest、Playwright実行
- **並列実行**: バックエンド・フロントエンドテストの高速化
- **キャッシュ戦略**: uv・pnpm依存関係のキャッシュによる実行時間短縮

### 関連ドキュメント
- [`docs/`](docs/) - 設計ドキュメント・アーキテクチャ詳細
- [`specs/`](specs/) - 要件仕様書・実装タスク管理
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) - CI設定詳細

---

**開発状況**: フロントエンド結果画面実装完了、バックエンドAPI開発中
**次期対応**: 診断フロー実装、LLM統合、エンドツーエンド結合

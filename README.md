# NightLoom

NightLoom は、分岐型の短編シナリオ体験を通じてユーザーの意思決定傾向を観測し、AI が動的に評価軸とタイプ分類を生成する Web アプリケーションです。MVP では 4 シーン構成の診断フローと高速なフェイルオーバーを備えた SPA を目標に開発を進めています。

## 実装状況

### Phase 6 Polish完了機能 ✅

**コア機能**
- **結果画面表示機能**: TypeCard、AxisScoreItem、AxesScores、ResultScreen コンポーネントの完全実装
- **ActionButtonsコンポーネント**: 独立したアクション実行機能（再診断・リトライ）、WCAG AA準拠アクセシビリティ
- **診断フロー**: 4シーン構成の診断体験とセッション管理
- **API システム**: FastAPI + Next.js統合、包括的エラーハンドリング
- **テーマシステム**: 複数テーマ対応とダイナミック切り替え機能

**品質・パフォーマンス強化**
- **テストカバレッジ**: 52+アクセシビリティテスト全合格（Jest + Testing Library + Playwright + axe-core）
- **アクセシビリティ**: WCAG 2.1 AA準拠100%達成、スクリーンリーダー完全対応、キーボード操作完全対応
- **パフォーマンス最適化**: React.memo/useCallback適用済み、不要な再レンダリング防止、メモリリーク対策完了
- **コード品質**: TypeScript strict mode完全準拠、ESLint エラーゼロ、未使用インポート削除完了
- **レスポンシブデザイン**: 360px+ビューポート完全対応、モバイル最適化
- **パフォーマンス監視**: Web Vitals収集、API遅延追跡、包括的メトリクス
- **セキュリティ強化**: 入力検証、レート制限、セッション保護、CSPヘッダー
- **モーション配慮**: prefers-reduced-motion完全対応

**運用・監視**
- **包括的ロギング**: 構造化ログ、メトリクス収集、フォールバック監視
- **プロダクションビルド**: バンドル最適化、コード分割、Tree Shaking、セキュリティヘッダー完全実装
- **デプロイ準備**: 本番環境対応完了、高度なキャッシュ戦略、パフォーマンス予算管理

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

### フロントエンド
| 技術 | バージョン | 用途 |
| --- | --- | --- |
| Next.js | 14 | App Router, React Server Components |
| React | 18 | UI フレームワーク |
| TypeScript | 5.5+ | 型安全性 |
| Tailwind CSS | 3.4+ | スタイリング + レスポンシブ |
| Jest + Testing Library | 最新 | ユニットテスト |
| Playwright | 最新 | E2Eテスト + アクセシビリティ |

### バックエンド
| 技術 | バージョン | 用途 |
| --- | --- | --- |
| Python | 3.12 | メイン言語 |
| FastAPI | 最新 | API フレームワーク |
| Uvicorn | 最新 | ASGI サーバー |
| Pydantic | 最新 | データ検証 |
| pytest + httpx | 最新 | テスト |

### 開発・運用
| 技術 | 用途 |
| --- | --- |
| uv | Python パッケージ管理 |
| pnpm | Node.js ワークスペース管理 |
| GitHub Actions | CI/CD |
| ESLint + Prettier | コード品質 |

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

## アーキテクチャ・品質保証

### システム設計
- **フロントエンド**: Next.js 14 App Router + React Server Components
- **バックエンド**: FastAPI + Python 3.12 + 非同期処理
- **API通信**: RESTful API + 構造化エラーレスポンス
- **状態管理**: React Context + クライアント状態管理
- **セキュリティ**: レート制限 + 入力検証 + CSP ヘッダー

### 品質保証戦略

**テスト階層**
| テスト種別 | 対象 | ツール | カバレッジ |
|------------|------|--------|------------|
| ユニットテスト | コンポーネント・関数 | Jest + Testing Library | 90%+ |
| 統合テスト | API・フロー | pytest + MSW | 85%+ |
| E2Eテスト | ユーザージャーニー | Playwright | 主要フロー100% |
| アクセシビリティ | WCAG準拠 | axe-core + 手動 | AA準拠 |
| パフォーマンス | Web Vitals | 自動監視 | 継続監視 |

**品質ゲート**
- **TypeScript**: 型エラー0
- **ESLint**: ルール違反0
- **テスト**: 全テスト通過
- **アクセシビリティ**: axe-core違反0
- **パフォーマンス**: Core Web Vitals "Good"

### 監視・運用

**パフォーマンス監視**
- Web Vitals (FCP, LCP, FID, CLS)
- API レスポンス時間 (p95 ≤ 800ms)
- フロントエンド描画時間
- バックエンド処理時間

**セキュリティ監視**
- レート制限状況
- 異常アクセス検出
- 入力検証エラー
- セッション セキュリティ

**品質メトリクス**
- テストカバレッジ継続監視
- アクセシビリティスコア
- パフォーマンス予算管理
- エラー率・成功率

### 関連ドキュメント
- [`docs/`](docs/) - 設計ドキュメント・アーキテクチャ詳細
- [`specs/`](specs/) - 要件仕様書・実装タスク管理
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) - CI設定詳細

---

## Phase 6 完了状況

**✅ 完了項目**
- 包括的ロギング・メトリクス収集
- レスポンシブデザイン・モバイル最適化（360px+対応）
- モーション配慮設計（prefers-reduced-motion）
- パフォーマンス監視・遅延追跡
- セキュリティ強化（入力検証・レート制限・セッション保護）
- パフォーマンス最適化（Next.js設定・バンドル最適化）

**🔄 継続監視項目**
- パフォーマンス目標達成状況
- セキュリティイベント監視
- アクセシビリティ準拠継続
- テストカバレッジ維持

**品質レベル**: Production Ready
**次期フェーズ**: LLM統合・本格運用準備

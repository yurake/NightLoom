# Implementation Plan: NightLoom結果画面表示機能

**Branch**: `002-nightloom-kekka-gamen-hyoji` | **Date**: 2025-10-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-nightloom-kekka-gamen-hyoji/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

NightLoomプロジェクトの結果画面表示機能を実装する。ユーザーが4シーン診断を完了後、軸スコア・タイプ分類結果を視覚的に表示し、プログレスバーアニメーション・再診断機能を提供する。Next.js 14 + TypeScript + Tailwind CSSによるレスポンシブSPA実装。

## Technical Context

**Language/Version**: TypeScript 5.0+ / JavaScript ES2022 (Next.js 14 App Router)
**Primary Dependencies**: React 18, Next.js 14, Tailwind CSS 3.0+, Jest, Playwright
**Storage**: セッション内一時データ保持（永続化なし）
**Testing**: Jest (Unit), Playwright (E2E), React Testing Library (Component)
**Target Platform**: Web Browser (Chrome 90+, Firefox 88+, Safari 14+, iOS Safari, Android Chrome)
**Project Type**: Web Application (フロントエンド単体機能)
**Performance Goals**: 結果画面レンダリング <500ms, スコアバーアニメーション 1秒±50ms, 初回読み込み <1s
**Constraints**: モバイル表示幅360px以上対応, アクセシビリティWCAG AA準拠, セッション内メモリ管理
**Scale/Scope**: 単一機能（結果表示画面）、6コンポーネント、2-6軸動的レンダリング

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Phase 0 初期チェック (✅ 完了)
**✅ 日本語統一**: すべてのコード、コメント、ドキュメントは日本語で統一済み
**✅ TDD原則**: テスト先行開発フローを適用（Jest単体テスト → 実装 → E2Eテスト）
**✅ ライブラリ優先**: Reactコンポーネントを独立ライブラリとして設計
**✅ CLIインターフェース**: Next.jsのnpm scriptsでCLI機能を提供
**✅ 統合テスト必須**: API結合、コンポーネント統合、E2Eテストを実装

### Phase 1 設計完了後チェック (✅ 完了)

#### I. 日本語統一 (✅ 準拠)
- 仕様書・設計書・API契約すべて日本語記述
- TypeScript型定義のコメント・説明は日本語
- エラーメッセージ・UI文言は日本語統一
- 技術文書（research.md, quickstart.md）は日本語

#### II. TDD原則 (✅ 準拠)
- テスト先行開発フローを明確化（quickstart.md Phase 1-4）
- Jest単体テスト → 実装 → E2Eテストの順序を規定
- 各コンポーネントに対応するテストファイル設計済み
- `RED-GREEN-REFACTOR`サイクル適用方針

#### III. ライブラリ優先 (✅ 準拠)
- ResultScreen、TypeCard、AxesScores等を独立コンポーネントとして設計
- 各コンポーネントは自己完結し、独立してテスト可能
- 再利用可能なAPI clientライブラリ（SessionApiClient）を分離
- 型定義ライブラリ（result-types.ts）を独立化

#### IV. CLIインターフェース (✅ 準拠)
- Next.js標準npm scriptsでCLI機能を提供
  - `pnpm dev` - 開発サーバー起動
  - `pnpm test` - テスト実行
  - `pnpm build` - プロダクションビルド
  - `pnpm exec playwright test` - E2Eテスト実行
- JSON形式での設定・データ交換対応
- stdin/args → stdout形式のデバッグ出力

#### V. 統合テスト必須 (✅ 準拠)
- API統合テスト（SessionApiClient ↔ Backend API）
- コンポーネント統合テスト（React Testing Library）
- E2E統合テスト（Playwright、フルユーザーフロー）
- 契約テスト（OpenAPI仕様 ↔ 実装）

**憲法適合性**: 🟢 完全準拠 - 違反事項なし

## Project Structure

### Documentation (this feature)

```
specs/002-nightloom-kekka-gamen-hyoji/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
frontend/
├── app/
│   ├── (play)/
│   │   ├── result/
│   │   │   └── page.tsx          # 結果画面メインページ
│   │   └── components/
│   │       ├── ResultScreen.tsx  # メインコンテナコンポーネント
│   │       ├── TypeCard.tsx      # タイプ情報表示カード
│   │       ├── AxesScores.tsx    # 軸スコア一覧表示
│   │       ├── AxisScoreItem.tsx # 個別軸スコア表示
│   │       └── ActionButtons.tsx # 再診断等アクション
│   ├── services/
│   │   └── session-api.ts        # セッションAPI クライアント
│   └── types/
│       └── result.ts             # 結果データ型定義
├── tests/
│   ├── components/
│   │   ├── ResultScreen.test.tsx
│   │   ├── TypeCard.test.tsx
│   │   ├── AxesScores.test.tsx
│   │   └── AxisScoreItem.test.tsx
│   └── services/
│       └── session-api.test.ts
└── e2e/
    └── result-screen.spec.ts     # E2E統合テスト
```

**Structure Decision**: Web Application（フロントエンド）構造を選択。既存のNext.js 14 App Router構成に結果画面機能を追加。コンポーネント分離によりテスト容易性と再利用性を確保。

## Complexity Tracking

*Constitution Check passed - no violations to justify*

該当なし：憲法の全原則に準拠

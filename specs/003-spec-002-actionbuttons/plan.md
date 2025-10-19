# Implementation Plan: spec 002未完了タスクの完了対応

**Branch**: `003-spec-002-actionbuttons` | **Date**: 2025-10-19 | **Spec**: [link](spec.md)
**Input**: Feature specification from `/specs/003-spec-002-actionbuttons/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

既存のspec 002実装の未完了項目を特定し、ActionButtonsコンポーネントの分離リファクタリングとチェックリスト完了確認を実施する。品質向上とTDD原則準拠を目的とし、既存機能を破綻させることなく段階的に改善する。

## Technical Context

**Language/Version**: TypeScript 5.0+, JavaScript ES2022  
**Primary Dependencies**: Next.js 14 (App Router), React 18, Tailwind CSS 3.0+, Jest, Playwright  
**Storage**: N/A (セッション内一時データのみ)  
**Testing**: Jest + Testing Library (単体), Playwright (E2E)  
**Target Platform**: Web (360px以上レスポンシブ対応)  
**Project Type**: Web (frontend/backendディレクトリ構造)  
**Performance Goals**: コンポーネント分離後も既存動作時間維持（±5%以内）  
**Constraints**: E2Eテスト実行時間5分以内、ESLintエラーゼロ維持  
**Scale/Scope**: 1個のActionButtonsコンポーネント分離、1個のチェックリスト完了確認

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Phase 0完了時):**
- [x] **Spec-First Delivery**: `specs/003-spec-002-actionbuttons/spec.md` が完成しており、3つの優先順位付きユーザーストーリーと明確な受け入れ条件が定義されている。
- [x] **Session Ephemerality & Data Minimalism**: ActionButtonsでのセッションクリーンアップ機能は既存実装を維持し、データ破棄と完全初期化を保証する。
- [x] **Resilient AI Operations**: 本機能はLLM依存なし。既存の結果画面表示とボタン機能のリファクタリングのみ。
- [x] **Performance & Responsiveness Guarantees**: 既存動作時間維持（±5%以内）を成功基準とし、性能劣化を防ぐ。
- [x] **Test & Observability Discipline**: Jest単体テスト100%カバレッジ、PlaywrightE2Eテスト100%成功率を目標とする。

**Phase 1設計完了後 再チェック:**
- [x] **Spec-First Delivery**: `research.md`, `data-model.md`, `quickstart.md`, `contracts/` が生成され、仕様書との整合性が確保されている。
- [x] **Session Ephemerality & Data Minimalism**: ActionButtonsPropsでonRestartコールバックによるセッションクリーンアップが設計されており、データ永続化を行わない。
- [x] **Resilient AI Operations**: 外部API依存なし。既存のセッション管理フローを維持し、フォールバック不要。
- [x] **Performance & Responsiveness Guarantees**: コンポーネント分離によるパフォーマンス測定計画とE2Eテストでの監視体制が設計済み。
- [x] **Test & Observability Discipline**: 単体テスト（Jest）、E2Eテスト（Playwright）、型安全性（TypeScript）の包括的テスト戦略が確立。

## Project Structure

### Documentation (this feature)

```
specs/003-spec-002-actionbuttons/
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
│   │   └── components/
│   │       ├── ActionButtons.tsx        # NEW: 分離されたコンポーネント
│   │       ├── ResultScreen.tsx         # MODIFIED: ActionButtons統合
│   │       ├── TypeCard.tsx             # EXISTING
│   │       ├── AxesScores.tsx           # EXISTING
│   │       └── AxisScoreItem.tsx        # EXISTING
│   └── types/
│       └── result.ts                    # EXISTING
├── tests/
│   ├── components/
│   │   └── result/
│   │       ├── ActionButtons.test.tsx   # NEW: 単体テスト
│   │       ├── ResultScreen.test.tsx    # MODIFIED: 統合テスト更新
│   │       ├── TypeCard.test.tsx        # EXISTING
│   │       ├── AxesScores.test.tsx      # EXISTING
│   │       └── AxisScoreItem.test.tsx   # EXISTING
│   └── mocks/
│       ├── handlers.ts                  # EXISTING
│       └── result-data.ts               # EXISTING
└── e2e/
    ├── results.spec.ts                  # EXISTING: 変更なし
    └── accessibility-keyboard.spec.ts   # EXISTING

specs/002-nightloom-kekka-gamen-hyoji/
└── checklists/
    └── implementation-progress.md       # MODIFIED: 完了項目更新
```

**Structure Decision**: 既存のNext.js 14 App Router構造を活用し、frontend/app/(play)/components/にActionButtonsコンポーネントを追加。テストはfrontend/tests/構造に従って配置。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

本機能では憲法違反はありません。既存実装のリファクタリングと品質改善に焦点を当てており、すべての憲法原則を満たしています。

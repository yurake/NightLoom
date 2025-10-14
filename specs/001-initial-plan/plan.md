# Implementation Plan: NightLoom MVP診断体験

**Branch**: `001-initial-plan` | **Date**: 2025-10-14 | **Spec**: [specs/001-initial-plan/spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-initial-plan/spec.md`

## Summary

NightLoom のMVPは、4シーン構成の診断フローでユーザーの意思決定傾向を観測し、動的に生成した評価軸とタイプ分類を結果画面で提示する体験を提供する。バックエンド（FastAPI + Python 3.12）とフロントエンド（Next.js 14 + TypeScript）を組み合わせ、LLMとの連携とフォールバック資材を活用して高速かつ安定した診断セッションを実現する。

## Technical Context

**Language/Version**: Python 3.12（backend）、TypeScript 5 / Next.js 14（frontend）  
**Primary Dependencies**: FastAPI、httpx、Pydantic、uv、React 18、Tailwind CSS、pnpm、Playwright  
**Storage**: セッション内メモリ保持（MVPでは永続化なし）  
**Testing**: pytest + httpx/respx、Jest + Testing Library、Playwright  
**Target Platform**: Web SPA（モバイル360px以上〜デスクトップ）  
**Project Type**: Webアプリケーション（backend + frontend モノレポ）  
**Performance Goals**: シーン取得 p95 ≤ 800ms、結果生成 p95 ≤ 1.2s、セッション完了 p95 ≤ 4.5s  
**Constraints**: セッションデータは非永続、LLM失敗時フォールバック必須、アクセシビリティ（ARIA/キーボード順）、360px以上レスポンシブ対応  
**Scale/Scope**: 同時セッション10件想定、MVP画面6枚（初期プロンプト + シーン×4 + 結果）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Spec-First Delivery**: `specs/001-initial-plan/spec.md` を唯一の基準とし、Phase 0 で clarifications 結果を `clarification-results.md` に同期することを計画。
- [x] **Session Ephemerality & Data Minimalism**: FR-008 / FR-012 でセッション破棄と再診断初期化を要求し、設計で明示する。
- [x] **Resilient AI Operations**: LLM再試行・フォールバック・観測ログ（FR-007, FR-011）を実装に織り込み、リスク対策を定義。
- [x] **Performance & Responsiveness Guarantees**: Performance Targets に p95 指標を設定し、計測計画（ログ/メトリクス）を策定する。
- [x] **Test & Observability Discipline**: pytest/Jest/Playwright を活用したテスト層とフォールバック監視メトリクスを本計画で整備する。

## Project Structure

### Documentation (this feature)

```
specs/001-initial-plan/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md  (後続フローで生成)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── clients/
│   └── config/
└── tests/

frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── services/
│   └── theme/
└── tests/
    ├── unit/
    └── e2e/

shared/            # タイプ/スキーマ共有予定
docs/              # 要件・設計ガイド
```

**Structure Decision**: Webアプリ構成（`backend/` + `frontend/`）を維持し、LLM連携やフォールバック資材は backend/services 配下、UIテーマと状態管理は frontend/src/app 配下で実装する。共有スキーマは将来的に `shared/` へ集約する。

## Complexity Tracking

（該当なし）

---

## Phase 0 – Research Workflow

1. `docs/requirements/overview.md` と `docs/design/overview.md` を精読し、LLMフォールバック・セッション管理・パフォーマンス指標を確認。
2. `specs/001-initial-plan/clarification-results.md` に曖昧性が追加された場合は直ちに同期。現状は未解決事項なし。
3. 研究ログ（research.md）に以下を記録済み:
   - セッション永続化を見送る判断
   - LLM再試行 + フォールバック戦略
   - パフォーマンス計測と監視項目
   - UIテーマ適用ポリシー
   - UUIDv4 採用理由
4. 追加の不明点が発生した場合は `/specify/scripts/bash/clarify` 系のワークフローを再実行し、3 項目以内に収める。

## Phase 1 – Design & Contracts

- **Data Model**: `data-model.md` にセッション、シーン、選択肢、評価軸、タイプ、テーマのスキーマと状態遷移を定義。
- **API Contracts**: `contracts/session-api.yaml` に OpenAPI 3.1 形式で bootstrap/keyword/scene/result エンドポイントを記述。
- **Quickstart**: `quickstart.md` で backend/frontend のセットアップ手順とテストコマンドを整理。
- **Agent Context**: `.specify/scripts/bash/update-agent-context.sh codex` を実行し、AGENTS.md に最新技術スタックを反映（手動で簡潔に整形）。

### Post-Design Constitution Check

- Spec-First Delivery: research & clarifications が spec と同期済み。  
- Session Ephemerality: データモデルで永続化しない前提を明記済み。  
- Resilient AI Operations: contracts でフォールバック指標（fallbackUsed）を返却、ログ項目も定義。  
- Performance & Responsiveness: quickstart で計測確認方法を案内。  
- Test & Observability: テストコマンドとフォールバック検証手順を quickstart に含めた。

---

## Phase 2 – Planning Handoff

- 次フェーズで `/speckit.tasks` を実行し、ユーザーストーリー単位のタスク分解を行う。
- プレイブック実行前に `clarification-results.md` を確認し、新たな質問があれば先に解決する。

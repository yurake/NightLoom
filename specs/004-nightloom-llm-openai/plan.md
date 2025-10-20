# Implementation Plan: NightLoom外部LLMサービス統合

**Branch**: `004-nightloom-llm-openai` | **Date**: 2025-10-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-nightloom-llm-openai/spec.md`

## Summary

NightLoom診断システムの核となる、外部LLMサービス（OpenAI GPT-4、Anthropic Claude）との実統合を実現する。現在のMockLLMServiceを置き換えて、真の動的キーワード生成、評価軸作成、シナリオ生成、結果分析を提供し、ユーザーごとに完全にユニークな診断体験を実現する。環境変数ベースの設定管理、95%レート制限でのフォールバック、テンプレート化プロンプトシステムにより、堅牢かつ柔軟な実装を行う。

## Technical Context

**Language/Version**: Python 3.12（backend）、TypeScript 5（frontend）
**Primary Dependencies**: FastAPI、httpx、Pydantic、OpenAI SDK、Anthropic SDK、Next.js 14、React 18
**Storage**: セッション内メモリ（非永続化）、プロンプトテンプレート（ファイル）
**Testing**: pytest + httpx/respx（backend）、Jest + Testing Library（frontend）、Playwright（E2E）
**Target Platform**: Web アプリケーション（バックエンドサーバー + フロントエンド SPA）
**Project Type**: Web（backend + frontend構成）
**Performance Goals**: LLM API呼び出し p95 < 5s、全診断完了 p95 < 8s、API使用コスト < 0.05USD/セッション
**Constraints**: レート制限 95%でフォールバック、5秒タイムアウト、形式検証のみ、既存フォールバック資産維持
**Scale/Scope**: 同時セッション数10-50想定、4つのLLM統合ポイント、テンプレート化プロンプト管理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Spec-First Delivery**: `specs/004-nightloom-llm-openai/spec.md` に明確化結果が統合済み、P1-P4優先順位付きユーザーストーリーと受け入れ条件が完備。
- [x] **Session Ephemerality & Data Minimalism**: 既存セッション管理システムを継承し、LLM応答データもセッション内一時保持のみ。永続化なし設計を維持。
- [x] **Resilient AI Operations**: FR-006/FR-007で1回リトライ+5秒タイムアウト+フォールバック資産使用を規定。API使用量監視とレート制限対応も完備。
- [x] **Performance & Responsiveness Guarantees**: SC-006で全LLM処理含む診断完了 p95 < 8s設定。既存結果画面500ms要件は継承。
- [x] **Test & Observability Discipline**: 既存pytest/Jest/Playwrightテスト基盤活用。SC-001～008で測定可能な成功基準設定。API使用量・レート制限・生成品質の監視項目明示。

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
backend/
├── app/
│   ├── clients/
│   │   ├── llm.py           # 拡張: ExternalLLMService実装
│   │   └── openai_client.py # 新規: OpenAI SDK統合
│   │   └── anthropic_client.py # 新規: Anthropic SDK統合
│   ├── services/
│   │   ├── session.py       # 拡張: LLMサービス切り替え
│   │   └── prompt_manager.py # 新規: テンプレート管理
│   ├── config/
│   │   └── llm_config.py    # 新規: プロバイダー設定
│   └── templates/
│       └── prompts/         # 新規: プロンプトテンプレート
└── tests/
    ├── unit/
    │   ├── test_llm_clients.py
    │   └── test_prompt_manager.py
    └── integration/
        └── test_llm_integration.py

frontend/
├── app/
│   ├── services/
│   │   └── sessionClient.ts # 変更なし（既存API継承）
│   └── components/          # 変更なし（結果表示は既存）
└── tests/
    └── integration/
        └── llm_integration.test.tsx
```

**Structure Decision**: 既存のWeb アプリケーション構成（backend/frontend）を維持し、LLM統合機能をbackend/app/clients配下に追加。フロントエンドは既存APIとの互換性維持により変更最小限。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

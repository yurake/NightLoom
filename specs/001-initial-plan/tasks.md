---
description: "Task list template for feature implementation"
---

# Tasks: NightLoom MVP診断体験

**Input**: Design documents from `/specs/001-initial-plan/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: NightLoom 憲章に従い、pytest / Jest / Playwright 等のテストと主要メトリクス収集は必須。各ユーザーストーリーでテストタスクを定義し、Failing First を実践する。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 共通データモデルとインフラを整備し、全ユーザーストーリーの土台を構築する

- [ ] T001 [Setup] Create core Pydantic schemas (`backend/app/models/session.py`) covering Session, Scene, Choice, AxisScore, TypeProfile
- [ ] T002 [Setup] Implement in-memory session store with state guard helpers (`backend/app/services/session_store.py`)
- [ ] T003 [P] [Setup] Add fallback asset definitions (axes, scenes, types) (`backend/app/services/fallback_assets.py`)
- [ ] T004 [P] [Setup] Scaffold HTTP client wrapper for external LLM calls (`backend/app/clients/base.py`)
- [ ] T005 [P] [Setup] Create frontend session API client stub (`frontend/app/services/sessionClient.ts`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: LLM 連携・計測・共有サービスを構築し、各ストーリー実装の前提条件を満たす  
**⚠️ CRITICAL**: このフェーズ完了までユーザーストーリー着手禁止

- [ ] T006 [Foundational] Implement LLMService abstraction with retry + timeout (`backend/app/clients/llm.py`)
- [ ] T007 [Foundational] Implement SessionService skeleton (start/load/record/result signatures) (`backend/app/services/session.py`)
- [ ] T008 [Foundational] Implement scoring service + normalization utilities (`backend/app/services/scoring.py`)
- [ ] T009 [Foundational] Implement typing service with dynamic thresholding (`backend/app/services/typing.py`)
- [ ] T010 [P] [Foundational] Add structured logging & metrics hook (fallback flags, latency) (`backend/app/services/observability.py`)
- [ ] T011 [P] [Foundational] Create React session context + reducer (`frontend/app/state/SessionContext.tsx`)

**Checkpoint**: Session/LLM services, scoring/typing、フロントの状態管理基盤が揃ったらユーザーストーリー実装へ進む

---

## Phase 3: User Story 1 - 初回アクセスで診断を開始する (Priority: P1) 🎯 MVP

**Goal**: 新規ユーザーがセッションを開始し、初期キーワード候補とシーン1を取得できる

**Independent Test**: `/api/sessions/start` → 初期候補提示 → `/api/sessions/{id}/keyword` でシーン1が得られ、フロントから手動テスト＆Playwrightで検証可能

### Tests for User Story 1 (必須: Fail First) ⚠️

- [ ] T012 [P] [US1] Write backend integration test for `/api/sessions/start` (`backend/tests/api/test_bootstrap.py`)
- [ ] T013 [P] [US1] Write Playwright test for bootstrap flow (`frontend/e2e/bootstrap.spec.ts`)

### Implementation for User Story 1

- [ ] T014 [US1] Implement `SessionService.start_session` to call LLM/fallback + seed keyword scores (`backend/app/services/session.py`)
- [ ] T015 [US1] Implement `/session/bootstrap` endpoint returning BootstrapResponse (`backend/app/api/bootstrap.py`)
- [ ] T016 [US1] Implement `/session/{session_id}/keyword` endpoint to confirm seed word + return scene1 (`backend/app/api/keyword.py`)
- [ ] T017 [P] [US1] Implement bootstrap observability logs (fallbackUsed, latency) (`backend/app/services/observability.py`)
- [ ] T018 [US1] Implement frontend bootstrap hook & API wiring (`frontend/app/services/sessionClient.ts`)
- [ ] T019 [US1] Build InitialPromptScreen UI with keyword candidates & custom input (`frontend/app/(play)/page.tsx`)
- [ ] T020 [P] [US1] Add Jest tests for InitialPromptScreen interactions (`frontend/tests/initialPrompt.test.tsx`)

**Checkpoint**: ブートストラップ API と初期プロンプト UI が独立して動作、テストが緑になったら US2 へ

---

## Phase 4: User Story 2 - 4シーンの選択体験を完走する (Priority: P2)

**Goal**: ユーザーが各シーンで選択し、セッション状態が進行・記録される

**Independent Test**: `/api/sessions/{id}/scenes/{n}` と `/choice` を通じて4シーン完走、フロントで進捗を確認しPlaywrightで自動化

### Tests for User Story 2 (必須: Fail First) ⚠️

- [ ] T021 [P] [US2] Add backend tests for scene retrieval/choice (`backend/tests/api/test_scene_flow.py`)
- [ ] T022 [P] [US2] Add Playwright flow covering 4 scene progression (`frontend/e2e/scene-flow.spec.ts`)

### Implementation for User Story 2

- [ ] T023 [US2] Extend SessionStore to persist choices + enforce state guards (`backend/app/services/session_store.py`)
- [ ] T024 [US2] Implement SessionService.load_scene / record_choice logic (`backend/app/services/session.py`)
- [ ] T025 [US2] Add `/session/{session_id}/scenes/{scene_index}` GET endpoint (`backend/app/api/scene.py`)
- [ ] T026 [US2] Add `/session/{session_id}/scenes/{scene_index}/choice` POST endpoint (`backend/app/api/scene.py`)
- [ ] T027 [P] [US2] Log scene progression + retry metadata (`backend/app/services/observability.py`)
- [ ] T028 [US2] Build SceneScreen component with loading/error states (`frontend/app/components/SceneScreen.tsx`)
- [ ] T029 [US2] Wire SessionContext reducer/actions for scene progression (`frontend/app/state/SessionContext.tsx`)
- [ ] T030 [P] [US2] Add Jest tests for reducer and SceneScreen interactions (`frontend/tests/sceneFlow.test.tsx`)

**Checkpoint**: 4シーン進行が独立して完遂・テスト緑 → US3 へ

---

## Phase 5: User Story 3 - 結果と学びを受け取り次アクションへ進む (Priority: P3)

**Goal**: スコアリング・タイプ分類を生成し、結果画面で表示。再診断導線とフォールバックも提供

**Independent Test**: `/api/sessions/{id}/result` がスコア/タイプを返却し、結果画面でアニメーション表示＆再診断ボタンが機能する

### Tests for User Story 3 (必須: Fail First) ⚠️

- [ ] T031 [P] [US3] Add backend tests for result generation + fallback (`backend/tests/api/test_result.py`)
- [ ] T032 [P] [US3] Add Jest tests for ResultScreen axis/type rendering (`frontend/tests/resultScreen.test.tsx`)
- [ ] T033 [P] [US3] Extend Playwright test covering result display + retry (`frontend/e2e/result-flow.spec.ts`)

### Implementation for User Story 3

- [ ] T034 [US3] Implement scoring pipeline (raw → normalized) (`backend/app/services/scoring.py`)
- [ ] T035 [US3] Implement typing pipeline + fallback presets (`backend/app/services/typing.py`)
- [ ] T036 [US3] Implement `/session/{session_id}/result` endpoint returning ResultResponse (`backend/app/api/result.py`)
- [ ] T037 [US3] Emit fallback flags + metrics for result generation (`backend/app/services/observability.py`)
- [ ] T038 [US3] Build ResultScreen component with animated axis bars (`frontend/app/result/page.tsx`)
- [ ] T039 [US3] Implement retry handler that replaces history + resets SessionContext (`frontend/app/result/page.tsx`)
- [ ] T040 [P] [US3] Add accessibility labels + prefers-reduced-motion handling (`frontend/app/result/page.tsx`)

**Checkpoint**: 結果生成と再診断導線が動作し、US1〜US3 が独立してデリバリー可能

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: 全体品質の底上げとドキュメント更新

- [ ] T041 [P] Update quickstart.md & README with final API flow (`specs/001-initial-plan/quickstart.md`, `README.md`)
- [ ] T042 [P] Add structured metrics exporter / dashboards for latency & fallback率 (`backend/app/services/observability.py`, monitoring setup)
- [ ] T043 [P] Execute accessibility audit (axe / Lighthouse) and address findings (frontend)
- [ ] T044 [P] Performance profiling for result animation + API p95 targets (frontend + backend)
- [ ] T045 [P] Prepare release notes / change log summarizing MVP delivery (`docs/notes/YYYYMMDD-nightloom-mvp.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → User story phases → Polish
- User stories execute sequentially by priority: US1 → US2 → US3
- Each user story requires preceding phases complete; later stories depend on earlier story infrastructure

### User Story Dependencies

- **US1 (P1)**: 基礎インフラが整えば単独でリリース可能（MVP）
- **US2 (P2)**: US1 完了後にのみ着手、シーン進行の追加価値
- **US3 (P3)**: US1/US2 の上に乗る結果生成・再診断機能

### Within Each User Story

- Tests (Fail First) → Services/Reducers → API エンドポイント → UI 実装 → 観測/アクセシビリティ
- 同一ファイル内編集は [P] を付与せず、順序を守る

### Parallel Opportunities

- [P] タグのタスクは別ファイル作業のため並行化可  
- 例: US1 では `initialPrompt` フロント実装 (T019) と Playwright テスト (T013) を別メンバーで実施可能

---

## Parallel Execution Examples

### User Story 1
- `T018 [US1]` (frontend API hook) と `T017 [US1]` (observability) を並行で着手可能

### User Story 2
- `T028 [US2]` SceneScreen UI と `T029 [US2]` SessionContext reducer は別ファイルのため並行化可

### User Story 3
- `T038 [US3]` ResultScreen UI と `T037 [US3]` 監視追加を別メンバーが実装可能

---

## Implementation Strategy

1. **MVP First**: US1 を完成させ、初期プロンプトとブートストラップ API をデリバリーしてユーザーテスト可能な状態にする  
2. **Incremental Delivery**: US2, US3 を順に追加し、各フェーズで Playwright を使った自動検証を実行  
3. **Polish**: メトリクス・アクセシビリティ・ドキュメントを仕上げ、MVP を本番導入可能な品質へ引き上げる

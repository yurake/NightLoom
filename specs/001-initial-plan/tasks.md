# Tasks: NightLoom MVP診断体験

**Input**: Design documents from `/specs/001-initial-plan/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: NightLoom 憲章に従い、pytest / Jest / Playwright 等のテストと主要メトリクス収集は必須。各ユーザーストーリーでテストタスクを定義し、Failing First を実践する。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/app/`, `frontend/app/`
- Based on plan.md structure with FastAPI + Next.js 14

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify project structure matches plan.md specifications (backend/, frontend/, docs/, specs/)
- [x] T002 [P] Initialize backend Python 3.12 environment with uv and FastAPI dependencies
- [x] T003 [P] Initialize frontend Next.js 14 project with TypeScript, Tailwind CSS, pnpm dependencies
- [x] T004 [P] Configure linting, formatting, and pre-commit hooks for both backend and frontend
- [x] T005 [P] Setup test frameworks: pytest + respx for backend, Jest + Testing Library + Playwright for frontend

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create FastAPI application structure in `backend/app/main.py` with CORS and basic routing
- [x] T007 [P] Implement session storage service in `backend/app/services/session_store.py` (in-memory, ephemeral)
- [x] T008 [P] Create base data models in `backend/app/models/session.py` (Session, Scene, Choice, Axis, TypeProfile)
- [x] T009 [P] Setup LLM client abstraction in `backend/app/clients/llm.py` with retry and fallback logic
- [x] T010 [P] Implement fallback assets service in `backend/app/services/fallback_assets.py`
- [x] T011 [P] Create observability service in `backend/app/services/observability.py` for metrics and logging
- [x] T012 [P] Setup Next.js App Router structure in `frontend/app/` with layout and basic routing
- [x] T013 [P] Implement session context provider in `frontend/app/state/SessionContext.tsx`
- [x] T014 [P] Create theme provider in `frontend/app/theme/ThemeProvider.tsx` with theme tokens
- [x] T015 [P] Setup API client in `frontend/app/services/sessionClient.ts` with error handling
- [x] T016 Configure environment variables and API proxy settings for frontend-backend communication

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 初回アクセスで診断を開始する (Priority: P1) 🎯 MVP

**Goal**: 来訪ユーザーが NightLoom を開き、提示された初期キーワード候補または任意入力を用いて診断セッションを開始できる

**Independent Test**: 新規ユーザーがトップ画面からセッションを開始し、初期単語を選択すると最初のシーンが表示されることを確認すれば価値が成立する

### Tests for User Story 1 (必須: Fail First) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T017 [P] [US1] Contract test for `/api/sessions/start` endpoint in `backend/tests/api/test_bootstrap.py`
- [x] T018 [P] [US1] Contract test for `/api/sessions/{sessionId}/keyword` endpoint in `backend/tests/api/test_keyword.py`
- [x] T019 [P] [US1] Integration test for bootstrap flow in `frontend/tests/integration/bootstrap.test.tsx`
- [x] T020 [P] [US1] E2E test for session start flow in `frontend/e2e/bootstrap.spec.ts`

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement session bootstrap service in `backend/app/services/session.py`
- [x] T022 [P] [US1] Implement scoring service in `backend/app/services/scoring.py`
- [x] T023 [P] [US1] Implement typing service in `backend/app/services/typing.py`
- [x] T024 [US1] Create bootstrap API endpoint in `backend/app/api/bootstrap.py`
- [x] T025 [US1] Create keyword confirmation API endpoint in `backend/app/api/keyword.py`
- [x] T026 [P] [US1] Create main landing page in `frontend/app/(play)/page.tsx` with keyword selection UI
- [x] T027 [P] [US1] Implement bootstrap flow components and loading states
- [x] T028 [US1] Add form validation and error handling for keyword input
- [x] T029 [US1] Integrate session API client with bootstrap flow

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 4シーンの選択体験を完走する (Priority: P2)

**Goal**: ユーザーが各シーンで選択を行い、セッションステータス遷移とスコア集計が正しく進む

**Independent Test**: 任意のシーンで選択を行い、次シーンが表示され、内部でスコアが蓄積されることを確認できれば価値が成立する

### Tests for User Story 2 (必須: Fail First) ⚠️

- [ ] T030 [P] [US2] Contract test for `/api/sessions/{sessionId}/scenes/{sceneIndex}` endpoint in `backend/tests/api/test_scenes.py`
- [ ] T031 [P] [US2] Contract test for `/api/sessions/{sessionId}/scenes/{sceneIndex}/choice` endpoint in `backend/tests/api/test_choices.py`
- [ ] T032 [P] [US2] Integration test for scene progression flow in `frontend/tests/integration/scenes.test.tsx`
- [ ] T033 [P] [US2] E2E test for 4-scene completion flow in `frontend/e2e/scenes.spec.ts`

### Implementation for User Story 2

- [ ] T034 [US2] Extend session service with scene generation and choice recording in `backend/app/services/session.py`
- [ ] T035 [US2] Create scene retrieval API endpoint in `backend/app/api/scenes.py`
- [ ] T036 [US2] Create choice submission API endpoint in `backend/app/api/choices.py`
- [ ] T037 [P] [US2] Implement scene display components in `frontend/app/(play)/components/Scene.tsx`
- [ ] T038 [P] [US2] Implement choice selection components in `frontend/app/(play)/components/ChoiceOptions.tsx`
- [ ] T039 [P] [US2] Add progress indicator component in `frontend/app/(play)/components/ProgressIndicator.tsx`
- [ ] T040 [US2] Integrate scene API calls with session context and navigation
- [ ] T041 [US2] Add loading states and error handling for scene transitions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 結果と学びを受け取り次アクションへ進む (Priority: P3)

**Goal**: ユーザーが集計結果（評価軸・タイプ・キーワード）を理解し、再診断などの行動を選択できる

**Independent Test**: 4シーン完了後に結果画面へ遷移し、タイプ説明と評価軸スコアが表示され、「もう一度診断する」が機能すれば価値が成立する

### Tests for User Story 3 (必須: Fail First) ⚠️

- [ ] T042 [P] [US3] Contract test for `/api/sessions/{sessionId}/result` endpoint in `backend/tests/api/test_results.py`
- [ ] T043 [P] [US3] Integration test for result calculation and display in `frontend/tests/integration/results.test.tsx`
- [ ] T044 [P] [US3] E2E test for complete diagnosis flow including results in `frontend/e2e/results.spec.ts`

### Implementation for User Story 3

- [ ] T045 [US3] Extend session service with result generation and type profiling in `backend/app/services/session.py`
- [ ] T046 [US3] Create result retrieval API endpoint in `backend/app/api/results.py`
- [ ] T047 [P] [US3] Create result page in `frontend/app/(play)/result/page.tsx`
- [ ] T048 [P] [US3] Implement result display components in `frontend/app/(play)/components/ResultScreen.tsx`
- [ ] T049 [P] [US3] Implement axis scores component in `frontend/app/(play)/components/AxesScores.tsx`
- [ ] T050 [P] [US3] Implement type card component in `frontend/app/(play)/components/TypeCard.tsx`
- [ ] T051 [US3] Add "restart diagnosis" functionality with session cleanup
- [ ] T052 [US3] Integrate result API calls with navigation and session management

**Checkpoint**: All user stories should now be independently functional

---

**Checkpoint**: All user stories should now be independently functional

---

## Phase 3.5: Accessibility Implementation (FR-010 対応)

**Purpose**: アクセシビリティ基準の満足 (FR-010)

**Target**: WCAG 2.1 AA準拠の実装でスクリーンリーダー利用者が主要情報を把握可能に

### Tests for Accessibility (必須: Fail First) ⚠️

- [ ] T065 [P] Create axe-core automated accessibility tests in `frontend/tests/accessibility/axe.test.tsx`
- [ ] T066 [P] Create keyboard navigation E2E tests in `frontend/e2e/accessibility-keyboard.spec.ts`
- [ ] T067 [P] Create screen reader compatibility tests for result display
- [ ] T068 [P] Create color contrast validation tests for all theme variants

### Implementation for Accessibility

- [ ] T069 [P] **アクセシビリティ基盤実装**: WAI-ARIA属性の実装
  - 結果画面でのaria-label、role、aria-describedby の適用
  - ランドマークrole（main, navigation, complementary）の定義
  - 見出し構造（h1-h6）の階層化
  - タイプカードとスコア表示への適切なaria属性の付与

- [ ] T070 [P] **キーボードナビゲーション対応**
  - Tab順序の論理的な定義（診断開始 → 選択肢 → 結果表示 → 再診断）
  - Enterキー、Spaceキーでの選択肢操作
  - Escapeキーでのダイアログ・モーダル終了
  - フォーカストラップの実装（必要に応じて）

- [ ] T071 [P] **フォーカス管理の実装**
  - 可視フォーカス表示の確保（:focus-visible 対応）
  - ページ遷移時のフォーカス位置管理
  - スキップリンクの実装（「メインコンテンツへスキップ」）
  - フォーカス状態のアニメーション（prefers-reduced-motion 対応）

- [ ] T072 [P] **スクリーンリーダー対応**
  - 結果画面でのスコア読み上げ対応（「冒険性：75点、100点中」等）
  - 進行状況の音声通知（「4問中2問目」等）
  - エラーメッセージのaria-live対応
  - 動的コンテンツ更新時のスクリーンリーダー通知

### Accessibility Testing & Validation

- [ ] T073 [P] **自動アクセシビリティテスト**
  - axe-coreを使用したWCAG 2.1 AA準拠テスト
  - 色彩コントラスト比検証（4.5:1以上の確保）
  - HTMLセマンティクス検証

- [ ] T074 [P] **手動アクセシビリティテスト**
  - NVDA/JAWSでの画面読み上げテスト
  - キーボードオンリー操作テスト
  - ハイコントラストモードでの表示確認

**Dependencies**: Phase 3 (User Story 1-3) 完了後に実装開始
**FR-010 Coverage**: 結果画面でのARIA ラベル、キーボードフォーカス順、スクリーンリーダー対応を完全実装

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Add comprehensive logging and metrics collection across all endpoints
- [ ] T054 [P] Implement responsive design and mobile optimization for 360px+ viewports
- [ ] T055 [P] Implement `prefers-reduced-motion` support across animations
- [ ] T057 [P] Add performance monitoring and latency tracking
- [ ] T058 [P] Expand unit test coverage to 90%+ in `backend/tests/` and `frontend/tests/`
- [ ] T059 [P] Add fallback scenario testing and LLM failure simulation
- [ ] T060 [P] Documentation updates in `docs/` and `README.md`
- [ ] T061 Security hardening: input validation, rate limiting, session protection
- [ ] T062 Code cleanup and refactoring based on test results
- [ ] T063 Run quickstart.md validation and update setup instructions
- [ ] T064 Performance optimization based on p95 latency requirements (≤800ms scenes, ≤1.2s results)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 but should be independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints/components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Components within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for /api/sessions/start endpoint in backend/tests/api/test_bootstrap.py"
Task: "Contract test for /api/sessions/{sessionId}/keyword endpoint in backend/tests/api/test_keyword.py"
Task: "Integration test for bootstrap flow in frontend/tests/integration/bootstrap.test.tsx"
Task: "E2E test for session start flow in frontend/e2e/bootstrap.spec.ts"

# Launch all services for User Story 1 together:
Task: "Implement session bootstrap service in backend/app/services/session.py"
Task: "Implement scoring service in backend/app/services/scoring.py"
Task: "Implement typing service in backend/app/services/typing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Performance & Quality Targets

- **Latency**: Scene retrieval p95 ≤ 800ms, Result generation p95 ≤ 1.2s
- **Reliability**: 99% session completion rate with fallback support
- **Accessibility**: WCAG 2.1 AA compliance for core user flows
- **Responsiveness**: 360px+ mobile viewport support
- **Test Coverage**: 90%+ unit test coverage, E2E coverage of all user stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

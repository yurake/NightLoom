
# Tasks: NightLoom外部LLMサービス統合

**Input**: Design documents from `/specs/004-nightloom-llm-openai/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: NightLoom 憲章に従い、pytest / Jest / Playwright 等のテストと主要メトリクス収集は必須。各ユーザーストーリーでテストタスクを定義し、Failing First を実践する。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/app/`, `frontend/app/`
- Paths shown below assume Web app structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and LLM service dependencies

- [x] T001 Add OpenAI SDK dependency to backend/pyproject.toml with `uv add openai`
- [x] T002 Add Anthropic SDK dependency to backend/pyproject.toml with `uv add anthropic`
- [x] T003 [P] Add Jinja2 template engine to backend/pyproject.toml with `uv add jinja2`
- [x] T004 [P] Create prompt template directories: backend/app/templates/prompts/
- [x] T005 [P] Update environment configuration to include LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core LLM infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create LLMProvider configuration system in backend/app/models/llm_config.py
- [x] T007 Create base LLM client interface in backend/app/clients/llm_client.py
- [x] T008 [P] Create PromptTemplate management system in backend/app/services/prompt_template.py
- [x] T009 [P] Create APIUsageMetrics tracking in backend/app/services/llm_metrics.py
- [x] T010 [P] Extend Session model with LLM integration fields in backend/app/models/session.py
- [x] T011 Create ExternalLLMService base class in backend/app/services/external_llm.py
- [x] T012 [P] Create fallback content management in backend/app/services/fallback_manager.py
- [x] T013 Setup LLM request logging and monitoring in backend/app/middleware/llm_monitoring.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - OpenAI API統合による動的キーワード生成 (Priority: P1) 🎯 MVP ✅

**Goal**: ユーザーの初期文字入力に基づいてGPT-4が関連性の高いキーワード候補4つを動的生成

**Independent Test**: OpenAI APIキーを設定してセッション開始時に、初期文字「あ」から生成されるキーワードが固定候補と異なる動的な候補であることを確認

### Tests for User Story 1 (必須: Fail First) ⚠️ ✅

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US1] Contract test for /api/llm/generate/keywords endpoint in backend/tests/integration/test_llm_keywords.py
- [x] T015 [P] [US1] OpenAI client unit test with mock responses in backend/tests/unit/test_openai_client.py
- [x] T016 [P] [US1] Keyword generation fallback test in backend/tests/integration/test_keyword_fallback.py

### Implementation for User Story 1 ✅

- [x] T017 [P] [US1] Create OpenAI client implementation in backend/app/clients/openai_client.py
- [x] T018 [P] [US1] Create keyword generation prompt template in backend/templates/prompts/keyword_generation.jinja2
- [x] T019 [US1] Implement keyword generation service method in backend/app/services/external_llm.py (integrated)
- [x] T020 [US1] Update bootstrap API endpoint to use LLM keyword generation (integrated via service)
- [x] T021 [US1] Add error handling and fallback for keyword generation failures
- [x] T022 [US1] Add performance monitoring for keyword generation requests

**Checkpoint**: ✅ User Story 1 is fully functional and testable independently

---

## Phase 4: User Story 2 - 動的評価軸生成による個性化診断 (Priority: P2)

**Goal**: ユーザーが選択したキーワードに基づいて、GPT-4が2〜6軸の評価軸を動的生成

**Independent Test**: キーワード「愛」と「冒険」で別々にセッションを開始し、生成される評価軸が異なることを確認

### Tests for User Story 2 (必須: Fail First) ⚠️

- [x] T023 [P] [US2] Contract test for /api/llm/generate/axes endpoint in backend/tests/integration/test_llm_axes.py
- [x] T024 [P] [US2] Evaluation axis generation validation test in backend/tests/unit/test_axis_validation.py
- [x] T025 [P] [US2] Axis generation fallback test in backend/tests/integration/test_axis_fallback.py

### Implementation for User Story 2

- [x] T026 [P] [US2] Create axis generation prompt template in backend/templates/prompts/axis_creation.jinja2
- [x] T027 [US2] Implement axis generation service method in backend/app/services/external_llm.py (integrated)
- [x] T028 [US2] Create /api/llm/generate/axes API endpoint in backend/app/api/bootstrap.py
- [x] T029 [US2] Add axis validation and normalization (2-6 axes constraint)
- [x] T030 [US2] Integrate dynamic axes with existing session flow
- [x] T031 [US2] Add axis generation performance monitoring

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - AIシナリオ・選択肢生成による没入体験 (Priority: P3)

**Goal**: 各シーンで、選択されたキーワードと生成された評価軸に基づいて、GPT-4がリアルタイムでシナリオテキストと4つの選択肢を生成

**Independent Test**: 同じキーワードでも異なる評価軸設定で診断を実行し、シナリオ内容と選択肢が動的に変化することを確認

### Tests for User Story 3 (必須: Fail First) ⚠️

- [ ] T032 [P] [US3] Contract test for /api/llm/generate/scenario endpoint in backend/tests/integration/test_llm_scenarios.py
- [ ] T033 [P] [US3] Scenario generation continuity test in backend/tests/integration/test_scenario_continuity.py
- [ ] T034 [P] [US3] Choice weights validation test in backend/tests/unit/test_choice_weights.py

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create scenario generation prompt template in backend/app/templates/prompts/scenario_generation.j2
- [ ] T036 [US3] Implement scenario generation service method in backend/app/services/session.py
- [ ] T037 [US3] Create /api/llm/generate/scenario API endpoint in backend/app/api/scenes.py (extend existing)
- [ ] T038 [US3] Update scene flow to use dynamic scenarios in backend/app/api/scenes.py
- [ ] T039 [US3] Add choice weight validation and balancing
- [ ] T040 [US3] Integrate scenario continuity tracking across scenes
- [ ] T041 [US3] Add scenario generation performance monitoring

**Checkpoint**: All core user stories should now be independently functional

---

## Phase 6: User Story 4 - AI結果分析による洞察生成 (Priority: P4)

**Goal**: 4シーン完了後、ユーザーの選択パターンと評価軸スコアに基づいて、GPT-4が個別のタイプ分析とパーソナリティ洞察を生成

**Independent Test**: 同じスコアパターンでも異なるキーワード・軸設定で結果生成を実行し、異なる分析結果が得られることを確認

### Tests for User Story 4 (必須: Fail First) ⚠️

- [ ] T042 [P] [US4] Contract test for /api/llm/generate/result endpoint in backend/tests/integration/test_llm_results.py
- [ ] T043 [P] [US4] Personality analysis quality test in backend/tests/integration/test_analysis_quality.py
- [ ] T044 [P] [US4] Result generation fallback test in backend/tests/integration/test_result_fallback.py

### Implementation for User Story 4

- [ ] T045 [P] [US4] Create result analysis prompt template in backend/app/templates/prompts/result_analysis.j2
- [ ] T046 [US4] Implement result analysis service method in backend/app/services/session.py
- [ ] T047 [US4] Create /api/llm/generate/result API endpoint in backend/app/api/results.py (extend existing)
- [ ] T048 [US4] Update result generation to use AI analysis in backend/app/api/results.py
- [ ] T049 [US4] Add personality type validation and formatting
- [ ] T050 [US4] Integrate AI results with existing result display (frontend compatibility)
- [ ] T051 [US4] Add result generation performance monitoring

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Anthropic Integration & Provider Management

**Purpose**: Secondary LLM provider and advanced provider management

- [ ] T052 [P] Create Anthropic client implementation in backend/app/clients/anthropic_client.py
- [ ] T053 [P] Unit tests for Anthropic client in backend/tests/unit/test_anthropic_client.py
- [ ] T054 Implement provider switching logic in backend/app/services/session.py
- [ ] T055 Create LLM provider health check endpoints in backend/app/api/bootstrap.py
- [ ] T056 [P] Add rate limit monitoring and automatic fallback
- [ ] T057 [P] Create usage statistics API endpoints in backend/app/api/bootstrap.py
- [ ] T058 Integration tests for provider switching in backend/tests/integration/test_provider_switching.py

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T059 [P] Update API documentation with LLM endpoints in docs/
- [ ] T060 [P] Add comprehensive error handling for all LLM failures
- [ ] T061 [P] Implement cost tracking and session-based limits
- [ ] T062 [P] Add security validation for LLM-generated content
- [ ] T063 [P] Performance optimization for concurrent LLM requests
- [ ] T064 [P] Expand unit test coverage for all LLM components in backend/tests/unit/
- [ ] T065 [P] Create E2E tests for complete LLM diagnosis flow in frontend/e2e/
- [ ] T066 Run quickstart.md validation with LLM integration
- [ ] T067 [P] Instrument latency metrics for all LLM API calls
- [ ] T068 [P] Setup monitoring and alerting for LLM service health
- [ ] T069 Create production deployment checklist for LLM services

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Anthropic Integration (Phase 7)**: Can proceed after Foundational + US1 completion
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - MVP priority
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on keyword concepts from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses keywords and axes from US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Uses all previous generation data

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Prompt templates before service methods
- Service methods before API endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can be worked in priority order
- All tests for a user story marked [P] can run in parallel
- Templates and client implementations marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (after dependencies met)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (OpenAI keyword generation)
4. **STOP and VALIDATE**: Test User Story 1 independently with real OpenAI API
5. Deploy/demo dynamic keyword generation feature

### Incremental Delivery

1. Complete Setup + Foundational → LLM foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Dynamic keywords MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Dynamic evaluation axes)
4. Add User Story 3 → Test independently → Deploy/Demo (AI-generated scenarios)
5. Add User Story 4 → Test independently → Deploy/Demo (Complete AI diagnosis)
6. Each story adds significant AI capability without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Keywords - highest priority)
   - Developer B: User Story 2 (Axes - can work parallel after prompt templates)
   - Developer C: Anthropic integration (Phase 7)
3. Stories complete and integrate independently with existing diagnosis flow

---

## Notes

---
description: "Task list for NightLoom結果画面表示機能 implementation"
---

# Tasks: NightLoom結果画面表示機能

**Input**: Design documents from `/specs/002-nightloom-kekka-gamen-hyoji/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as per TDD constitution principle and feature specification requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/app/`, `frontend/tests/`
- Paths use Next.js 14 App Router structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] プロジェクト構造を確認し、必要なディレクトリを作成 (`frontend/app/(play)/components/`, `frontend/app/types/`, `frontend/app/services/`, `frontend/tests/components/result/`, `frontend/tests/services/`, `frontend/e2e/`)
- [x] T002 [P] 型定義ファイルを作成 (`frontend/app/types/result.ts`) - contracts/result-types.ts の内容を再エクスポート
- [x] T003 [P] モックデータファイルを作成 (`frontend/tests/mocks/result-data.ts`) - mockResult2Axes, mockResult6Axes をエクスポート
- [x] T004 [P] MSWセットアップファイルを作成 (`frontend/tests/mocks/handlers.ts`) - API モックハンドラー定義

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 SessionApiClient クラス基本実装 (`frontend/app/services/session-api.ts`) - fetch wrapper, error handling, timeout設定
- [x] T006 [P] SessionApiClient テスト作成 (`frontend/tests/services/session-api.test.ts`) - TDD: テスト先行作成、失敗確認
- [x] T007 SessionApiClient getResult メソッド実装 - GET /api/sessions/{sessionId}/result の統合
- [x] T008 [P] エラーハンドリングユーティリティ作成 (`frontend/app/utils/error-handler.ts`) - ErrorResponse 処理、fallback ロジック
- [x] T009 [P] データバリデーションユーティリティ作成 (`frontend/app/utils/validators.ts`) - isResultData, isAxisScore 型ガード実装

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 診断結果の基本表示 (Priority: P1) 🎯 MVP

**Goal**: ユーザーが4シーンの選択を完了した後、自分のタイプ分類と軸スコアを即座に確認できる

**Independent Test**: シーン4完了後に結果画面にアクセスし、タイプ名・説明・軸スコアが全て表示されることで独立して価値を提供する

### Tests for User Story 1 (TDD - テスト先行) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] TypeCard コンポーネントテスト作成 (`frontend/tests/components/result/TypeCard.test.tsx`) - タイプ名、説明、極性表示のテスト
- [ ] T011 [P] [US1] AxisScoreItem コンポーネントテスト作成 (`frontend/tests/components/result/AxisScoreItem.test.tsx`) - 軸名、スコア、方向性表示のテスト
- [ ] T012 [P] [US1] AxesScores コンポーネントテスト作成 (`frontend/tests/components/result/AxesScores.test.tsx`) - 2-6軸の動的レンダリングテスト
- [ ] T013 [US1] ResultScreen コンポーネントテスト作成 (`frontend/tests/components/result/ResultScreen.test.tsx`) - 統合表示、ローディング、エラー状態のテスト

### Implementation for User Story 1

- [ ] T014 [P] [US1] TypeCard コンポーネント実装 (`frontend/app/(play)/components/TypeCard.tsx`) - タイプ名、説明、極性バッジ、グラデーション背景
- [ ] T015 [P] [US1] AxisScoreItem コンポーネント基本実装 (`frontend/app/(play)/components/AxisScoreItem.tsx`) - 軸名、スコア数値、方向性表示（アニメーションなし）
- [ ] T016 [US1] AxesScores コンポーネント実装 (`frontend/app/(play)/components/AxesScores.tsx`) - AxisScoreItem の配列レンダリング、2-6軸対応
- [ ] T017 [US1] ResultScreen コンテナコンポーネント実装 (`frontend/app/(play)/components/ResultScreen.tsx`) - API呼び出し、状態管理、TypeCard + AxesScores 統合
- [ ] T018 [US1] LoadingIndicator コンポーネント実装 (`frontend/app/(play)/components/LoadingIndicator.tsx`) - API読み込み中の表示
- [ ] T019 [US1] ErrorMessage コンポーネント実装 (`frontend/app/(play)/components/ErrorMessage.tsx`) - エラー状態の表示、エラーコード別メッセージ
- [ ] T020 [US1] 結果画面ページ実装 (`frontend/app/(play)/result/page.tsx`) - ResultScreen の配置、sessionId 取得、Next.js App Router 統合
- [ ] T021 [US1] レスポンシブスタイル実装 (各コンポーネント) - 360px-1920px対応、Tailwind CSS breakpoints
- [ ] T022 [US1] US1統合テスト実行 - すべてのテストがパスすることを確認

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - スコア可視化とアニメーション (Priority: P2)

**Goal**: 各評価軸のスコアがプログレスバーでアニメーション付きで可視化され、ユーザーが直感的に理解できる

**Independent Test**: 結果画面読み込み時にスコアバーが0%から実際の値まで1秒でアニメーションすることで独立して価値を提供する

### Tests for User Story 2 (TDD - テスト先行) ⚠️

- [ ] T023 [P] [US2] スコアバーアニメーションテスト作成 (`frontend/tests/components/result/AxisScoreItem.test.tsx` に追加) - アニメーション開始、完了、タイミング検証
- [ ] T024 [P] [US2] プログレスバーアクセシビリティテスト作成 - aria-* 属性、role="progressbar" 検証

### Implementation for User Story 2

- [ ] T025 [US2] AxisScoreItem アニメーション機能追加 (`frontend/app/(play)/components/AxisScoreItem.tsx`) - CSS Transition + useEffect による1秒アニメーション実装
- [ ] T026 [US2] スコアバー視覚デザイン実装 - グラデーション背景、プログレスバー、easing: ease-out
- [ ] T027 [US2] アニメーション遅延制御実装 - 100ms遅延後開始、performance.mark() によるタイミング計測
- [ ] T028 [US2] アクセシビリティ属性追加 - aria-label, aria-valuenow, aria-valuemin, aria-valuemax, role="progressbar"
- [ ] T029 [US2] prefers-reduced-motion 対応実装 - CSS media query によるアニメーション無効化
- [ ] T030 [US2] US2統合テスト実行 - アニメーションテストがパスすることを確認

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 再診断機能 (Priority: P3)

**Goal**: ユーザーが結果を確認した後、簡単に新しい診断を開始できる

**Independent Test**: 結果画面から「もう一度診断する」ボタンをクリックして初期画面に戻ることで独立して価値を提供する

### Tests for User Story 3 (TDD - テスト先行) ⚠️

- [ ] T031 [P] [US3] ActionButtons コンポーネントテスト作成 (`frontend/tests/components/result/ActionButtons.test.tsx`) - ボタンクリック、ナビゲーション動作テスト
- [ ] T032 [US3] セッションクリーンアップテスト作成 - メモリクリア、LocalStorage削除、状態リセット検証

### Implementation for User Story 3

- [ ] T033 [US3] ActionButtons コンポーネント実装 (`frontend/app/(play)/components/ActionButtons.tsx`) - 「もう一度診断する」ボタン、useNavigate 統合
- [ ] T034 [US3] セッションクリーンアップ関数実装 (`frontend/app/utils/session-cleanup.ts`) - sessionId, 結果データ、LocalStorage クリア
- [ ] T035 [US3] ResultScreen に ActionButtons 統合 - 再診断ボタン配置、クリーンアップ処理呼び出し
- [ ] T036 [US3] 履歴置換によるブラウザバック無効化実装 - router.replace() 使用、セッション独立性保証
- [ ] T037 [US3] US3統合テスト実行 - 再診断フローがパスすることを確認

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: E2E Testing & Integration

**Purpose**: End-to-end validation of complete user flows

- [ ] T038 [P] E2Eテスト: 基本表示フロー (`frontend/e2e/result-screen.spec.ts`) - セッション完了 → 結果画面遷移 → タイプ・スコア表示確認
- [ ] T039 [P] E2Eテスト: アニメーション確認 - スコアバー1秒アニメーション、視覚的検証
- [ ] T040 [P] E2Eテスト: 再診断フロー - 「もう一度診断する」→ 初期画面遷移 → 新セッション作成確認
- [ ] T041 [P] E2Eテスト: エラー状態 - SESSION_NOT_FOUND, SESSION_NOT_COMPLETED, TYPE_GEN_FAILED の各エラー再現と表示確認
- [ ] T042 [P] E2Eテスト: レスポンシブ表示 - 360px, 768px, 1024px, 1920px 各幅での表示確認
- [ ] T043 [P] E2Eテスト: アクセシビリティ - axe-core によるWCAG AA準拠検証、キーボードナビゲーション確認
- [ ] T044 全E2Eテスト実行 - すべてのテストがパスすることを確認

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] パフォーマンス最適化: メモ化 - useMemo, useCallback 適用、不要な再レンダリング防止
- [ ] T046 [P] パフォーマンス最適化: バンドルサイズ - Dynamic Imports 適用、Code Splitting
- [ ] T047 [P] パフォーマンス最適化: メモリ管理 - WeakMap 使用、useEffect cleanup 実装
- [ ] T048 [P] コードクリーンアップ: TypeScript strict mode - 型エラー解消、any 削除
- [ ] T049 [P] コードクリーンアップ: Linting - ESLint エラー修正、Prettier フォーマット適用
- [ ] T050 [P] ドキュメント更新: コンポーネントJSDoc追加 - 各コンポーネントの使用方法、props説明
- [ ] T051 パフォーマンス計測実装 - performance.mark/measure による500ms要件検証
- [ ] T052 quickstart.md 検証実行 - ガイド通りにセットアップ・テストが完了することを確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **E2E Testing (Phase 6)**: Depends on all user stories being complete
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- コンポーネント実装前にテスト作成
- 基本コンポーネント（TypeCard, AxisScoreItem）before コンテナコンポーネント（ResultScreen）
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/components within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "TypeCard コンポーネントテスト作成 in frontend/tests/components/result/TypeCard.test.tsx"
Task: "AxisScoreItem コンポーネントテスト作成 in frontend/tests/components/result/AxisScoreItem.test.tsx"
Task: "AxesScores コンポーネントテスト作成 in frontend/tests/components/result/AxesScores.test.tsx"

# After tests fail, launch component implementations in parallel:
Task: "TypeCard コンポーネント実装 in frontend/app/(play)/components/TypeCard.tsx"
Task: "AxisScoreItem コンポーネント基本実装 in frontend/app/(play)/components/AxisScoreItem.tsx"
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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## TDD憲法準拠

本タスクリストはNightLoomプロジェクト憲法のTDD原則に完全準拠しています：

- ✅ **テスト先行**: すべてのUser Storyで実装前にテスト作成（T010-T013, T023-T024, T031-T032）
- ✅ **RED-GREEN-REFACTOR**: テスト失敗確認 → 実装 → リファクタリングのサイクル適用
- ✅ **統合テスト必須**: E2Eテスト（Phase 6）でシステム全体を検証

---

## 進捗追跡

実装を開始したら、各タスクの `[ ]` を `[x]` に変更してください。

例:
```markdown
- [x] T001 [P] プロジェクト構造を確認し、必要なディレクトリを作成
- [x] T002 [P] 型定義ファイルを作成
- [ ] T003 [P] モックデータファイルを作成
```

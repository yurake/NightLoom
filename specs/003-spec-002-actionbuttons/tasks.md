
---
description: "Task list for spec 002未完了タスクの完了対応 implementation"
---

# Tasks: spec 002未完了タスクの完了対応

**Input**: Design documents from `/specs/003-spec-002-actionbuttons/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as per TDD constitution principle and feature specification requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/app/`, `frontend/tests/`
- Paths use Next.js 14 App Router structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] プロジェクト構造を確認し、必要なディレクトリを作成 (`frontend/app/(play)/components/`, `frontend/tests/components/result/`)
- [x] T002 [P] 型定義ファイルを既存のresult.tsに統合 (`frontend/app/types/result.ts`) - contracts/action-buttons-types.ts の ActionButtonsProps を追加
- [x] T003 [P] 既存ResultScreenの実装状況確認 (`frontend/app/(play)/components/ResultScreen.tsx`) - 現在のボタン実装を分析

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 現在のResultScreen動作時間をベースライン測定 - パフォーマンス基準確立（±5%以内の要件）
- [x] T005 [P] 既存のresult画面テスト環境確認 (`frontend/tests/components/result/ResultScreen.test.tsx`) - 現在のテストカバレッジ分析
- [x] T006 [P] ESLint設定確認とベースラインエラー状況記録 - リファクタリング後のゼロエラー維持用

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - ActionButtonsコンポーネントのリファクタリング (Priority: P1) 🎯 MVP

**Goal**: 現在ResultScreen内に直接実装されている「もう一度診断する」ボタンを独立したActionButtonsコンポーネントに分離し、再利用性とテストのしやすさを向上させる

**Independent Test**: ActionButtonsコンポーネントを独立してテストでき、様々な状況（ローディング、エラー）での動作を検証できることで独立して価値を提供する

### Tests for User Story 1 (TDD - テスト先行) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] ActionButtons コンポーネントテスト作成 (`frontend/tests/components/result/ActionButtons.test.tsx`) - TDD: テスト先行作成、失敗確認
  - [x] ボタンレンダリング基本テスト
  - [x] onRestart コールバック実行テスト
  - [x] ローディング状態表示テスト
  - [x] エラー状態表示テスト
  - [x] 無効化状態テスト
  - [x] アクセシビリティ属性テスト (aria-label, data-testid)

### Implementation for User Story 1

- [x] T008 [US1] ActionButtons コンポーネント基本実装 (`frontend/app/(play)/components/ActionButtons.tsx`) - ActionButtonsProps インターフェースに基づく実装
  - [x] 基本的なボタンレンダリング
  - [x] onRestart コールバック処理
  - [x] useState による内部状態管理
  - [x] isLoading, isDisabled props 対応
  - [x] Tailwind CSS スタイル適用
- [x] T009 [US1] ActionButtons 状態管理実装 - ローディング、エラー、無効化状態の制御
  - [x] 内部ローディング状態管理
  - [x] エラーハンドリングと表示
  - [x] ボタン無効化ロジック
  - [x] 適切なメッセージ表示
- [x] T010 [US1] ActionButtons アクセシビリティ対応 - WCAG AA準拠の実装
  - [x] aria-label 属性設定
  - [x] data-testid 属性追加
  - [x] キーボードナビゲーション対応
  - [x] フォーカス管理
- [x] T011 [US1] ResultScreen バックアップ作成とActionButtons統合準備 (`frontend/app/(play)/components/ResultScreen.tsx`)
  - [x] 既存実装のバックアップ作成
  - [x] ActionButtons import 追加
  - [x] 既存ボタンコードの特定と分析
- [x] T012 [US1] ResultScreen ActionButtons 統合実装 - 既存ボタンをActionButtonsコンポーネントで置換
  - [x] 既存ボタンセクション削除
  - [x] ActionButtons コンポーネント配置
  - [x] onRestart ハンドラー実装
  - [x] props 渡し (isLoading, isDisabled)
- [x] T013 [US1] ResultScreen テスト更新 (`frontend/tests/components/result/ResultScreen.test.tsx`) - ActionButtons統合後のテスト修正
  - [x] ActionButtons統合テスト追加
  - [x] 既存テストの修正
  - [x] 統合動作確認テスト
- [x] T014 [US1] US1統合テスト実行 - すべてのテストがパスすることを確認
  - [x] 単体テスト実行 (ActionButtons.test.tsx)
  - [x] 統合テスト実行 (ResultScreen.test.tsx)
  - [x] 型チェック確認 (pnpm type-check)
  - [x] リント確認 (pnpm lint)
- [x] T015 [US1] パフォーマンス検証 - 既存動作時間との比較（±5%以内の確認）
  - [x] 分離前後の動作時間測定
  - [x] 成功基準達成確認
  - [x] 性能劣化なしの検証

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - spec 002チェックリスト項目の完了確認 (Priority: P2)

**Goal**: spec 002の実装進捗チェックリストで未完了となっている項目を検証し、実際の実装状況と一致させて完了状態を記録する

**Independent Test**: チェックリストの各項目を検証し、実装済み機能が正しく動作することを確認できることで独立して価値を提供する

### Tests for User Story 2 (TDD - テスト先行) ⚠️

- [x] T016 [P] [US2] チェックリスト検証ユーティリティテスト作成 (`frontend/tests/utils/checklist-verification.test.ts`) - チェックリスト項目検証ロジックのテスト
  - [x] 実装状況確認テスト
  - [x] 完了項目判定テスト
  - [x] 検証方法実行テスト

### Implementation for User Story 2

- [x] T017 [US2] チェックリスト検証ユーティリティ実装 (`frontend/app/utils/checklist-verification.ts`) - 実装状況確認と検証ロジック
  - [x] 既存コンポーネント存在確認
  - [x] テスト実行と結果確認
  - [x] 機能要件達成確認
  - [x] 成功基準達成確認
- [x] T018 [US2] spec 002 実装状況の包括的検証実行
  - [x] TypeCard コンポーネント実装確認
  - [x] AxesScores コンポーネント実装確認
  - [x] AxisScoreItem コンポーネント実装確認
  - [x] ResultScreen 統合確認
  - [x] 既存テスト実行確認
- [ ] T019 [US2] spec 002 チェックリスト更新 (`specs/002-nightloom-kekka-gamen-hyoji/checklists/implementation-progress.md`)
  - [ ] Phase 1 完了項目のマーク
  - [ ] Phase 2 完了項目のマーク
  - [ ] Phase 3 完了項目のマーク (ActionButtons含む)
  - [ ] 完了日の記録
  - [ ] 検証方法の記録
- [ ] T020 [US2] 機能要件と成功基準の最終検証
  - [ ] FR-001～FR-007 達成確認
  - [ ] SC-001～SC-004 達成確認
  - [ ] パフォーマンス基準確認
  - [ ] 品質ゲート通過確認
- [ ] T021 [US2] US2統合テスト実行 - チェックリスト完了確認の動作検証

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Quality Assurance & Polish

**Purpose**: Final validation and improvements that affect multiple user stories

- [ ] T022 [P] 全体統合テスト実行 - すべてのコンポーネントが正常連携することを確認
  - [ ] ActionButtons + ResultScreen 統合
  - [ ] 既存コンポーネント (TypeCard, AxesScores) との連携
  - [ ] セッションフロー全体の動作確認
- [ ] T023 [P] パフォーマンス最適化確認 - React.memo, useCallback 等の適用検討
  - [ ] 不要な再レンダリング防止
  - [ ] メモリ使用量確認
  - [ ] バンドルサイズ影響確認
- [ ] T024 [P] コードクリーンアップ - TypeScript strict mode, ESLint 完全準拠
  - [ ] 未使用インポート削除
  - [ ] 型エラー完全解消
  - [ ] ESLint エラーゼロ達成
- [ ] T025 [P] アクセシビリティ最終確認 - WCAG AA準拠の包括的チェック
  - [ ] キーボードナビゲーション全体確認
  - [ ] スクリーンリーダー対応確認
  - [ ] フォーカス管理確認
  - [ ] カラーコントラスト確認
- [ ] T026 プロダクションビルド確認 - デプロイ可能状態の検証
  - [ ] pnpm build 成功確認
  - [ ] バンドル最適化確認
  - [ ] 本番環境動作確認
- [ ] T027 ドキュメント更新 - README, コンポーネントドキュメント更新
  - [ ] ActionButtons 使用方法記載
  - [ ] プロジェクト構造更新
  - [ ] 開発者向けガイド更新

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-4)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Quality Assurance (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run parallel to US1, but benefits from US1 completion for accurate verification

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- コンポーネント実装前にテスト作成
- 基本機能 before 統合機能
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 and 2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/components within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "ActionButtons コンポーネントテスト作成 in frontend/tests/components/result/ActionButtons.test.tsx"

# After tests fail, launch component implementations in parallel:
Task: "ActionButtons コンポーネント基本実装 in frontend/app/(play)/components/ActionButtons.tsx"
Task: "ActionButtons 状態管理実装"
Task: "ActionButtons アクセシビリティ対応"
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
4. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (ActionButtons component refactoring)
   - Developer B: User Story 2 (Checklist completion verification)
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

- ✅ **テスト先行**: すべてのUser Storyで実装前にテスト作成（T007, T016）
- ✅ **RED-GREEN-REFACTOR**: テスト失敗確認 → 実装 → リファクタリングのサイクル適用
- ✅ **統合テスト必須**: 各User Story完了時と最終Phase 5で統合テスト実行

---

## 進捗追跡

実装を開始したら、各タスクの `[ ]` を `[x]` に変更してください。

例:
```markdown
- [x] T001 [P] プロジェクト構造を確認し、必要なディレクトリを作成
- [x] T002 [P] 型定義ファイルを既存のresult.tsに統合
- [ ] T003 [P] 既存ResultScreenの実装状況確認
```

---

## Summary

**Total Tasks**: 27
**User Story 1 Tasks**: 9 (T007-T015)
**User Story 2 Tasks**: 6 (T016-T021)
**Setup/Foundation Tasks**: 6 (T001-T006)
**Quality Assurance Tasks**: 6 (T022-T027)

**Suggested MVP Scope**: User Story 1のみ (ActionButtonsコンポーネント分離)
**Full Feature Scope**: User Story 1 + 2 (ActionButtons + チェックリスト完了)

**Estimated Timeline**:
- Setup + Foundation: 1時間
- User Story 1: 2-3時間 (TDD含む)
- User Story 2: 1-2時間
- Quality Assurance: 1時間
- **Total**: 5-7時間

**Key Success Criteria**:
- ActionButtons単体テストカバレッジ100%
- 既存機能の動作時間維持（±5%以内）
- ESLintエラーゼロ維持
- spec 002チェックリスト完了項目100%一致

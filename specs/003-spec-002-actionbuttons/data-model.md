# Data Model: spec 002未完了タスクの完了対応

**Date**: 2025-10-19  
**Phase**: Phase 1 - Design & Contracts  
**Feature**: ActionButtonsコンポーネント分離、チェックリスト完了確認

## Overview

本機能は既存データモデルを変更せず、コンポーネントインターフェースの定義とチェックリスト管理のエンティティのみを扱う。新しいデータ永続化や外部API統合は不要。

## Core Entities

### ActionButtonsProps

ActionButtonsコンポーネントのプロパティインターフェース。

**Purpose**: 分離されたActionButtonsコンポーネントの設定と動作制御

**Fields**:
- `onRestart: () => void | Promise<void>` - 再診断開始時のコールバック関数
- `onRetry?: () => void | Promise<void>` - リトライ実行時のコールバック関数（オプション）
- `isLoading?: boolean` - ローディング状態フラグ（デフォルト: false）
- `isDisabled?: boolean` - ボタン無効化フラグ（デフォルト: false）
- `variant?: 'primary' | 'secondary'` - ボタンスタイルバリアント（デフォルト: 'primary'）
- `className?: string` - 追加CSSクラス（オプション）

**Validation Rules**:
- `onRestart`は必須フィールド
- `isLoading`と`isDisabled`の両方がtrueの場合、`isDisabled`が優先
- `variant`は定義された値のみ受け入れ

**State Transitions**:
```
初期状態 → ローディング状態 → 完了状態
  ↓              ↓           ↓
無効状態 ←── エラー状態 ←── 失敗状態
```

### ImplementationChecklistItem

spec 002チェックリストの項目エンティティ。

**Purpose**: 実装進捗の追跡と完了状況の管理

**Fields**:
- `itemId: string` - チェックリスト項目の識別子
- `section: string` - 所属セクション（例: "Phase 1", "Phase 2"）
- `description: string` - 項目の説明
- `isCompleted: boolean` - 完了状態フラグ
- `completedDate?: string` - 完了日（ISO 8601形式）
- `verificationMethod: string` - 検証方法の説明
- `dependencies?: string[]` - 依存する他の項目のID配列

**State Transitions**:
```
未開始 → 進行中 → 完了
  ↓       ↓      ↓
 保留 → 再開 → 検証済み
```

## Component Interfaces

### ActionButtons Component

```typescript
interface ActionButtonsProps {
  /** 再診断開始時のコールバック */
  onRestart: () => void | Promise<void>;
  
  /** リトライ実行時のコールバック（オプション） */
  onRetry?: () => void | Promise<void>;
  
  /** ローディング状態 */
  isLoading?: boolean;
  
  /** ボタン無効化状態 */
  isDisabled?: boolean;
  
  /** ボタンスタイルバリアント */
  variant?: 'primary' | 'secondary';
  
  /** 追加CSSクラス */
  className?: string;
}

interface ActionButtonsState {
  /** 内部ローディング状態 */
  internalLoading: boolean;
  
  /** エラー状態 */
  error: string | null;
}
```

### Test Configuration Interfaces

```typescript
interface ChecklistUpdateRequest {
  /** 更新する項目のID配列 */
  itemIds: string[];
  
  /** 完了状態 */
  isCompleted: boolean;
  
  /** 完了日 */
  completedDate: string;
  
  /** 検証コメント */
  verificationComment?: string;
}
```

## Relationships

### ActionButtons ↔ ResultScreen
- **Type**: Composition (ResultScreenがActionButtonsを含む)
- **Cardinality**: 1:1
- **Direction**: ResultScreen → ActionButtons（propsを通じてデータ渡し）

### ImplementationChecklistItem ↔ Phase
- **Type**: Aggregation (PhaseがChecklistItemを含む)
- **Cardinality**: 1:N
- **Direction**: Phase → ImplementationChecklistItem（セクション単位での管理）

## Data Flow

### ActionButtons Component Data Flow

```
1. ResultScreen → ActionButtonsProps
   - onRestart関数を渡す
   - isLoading, isDisabled状態を渡す

2. ActionButtons → User Interaction
   - ボタンクリックイベントを処理
   - 状態に応じてUI更新

3. ActionButtons → Parent Callback
   - onRestart()コールバック実行
   - 非同期処理の結果を親に通知
```

### Checklist Management Data Flow

```
1. Implementation → Verification
   - 機能実装の完了
   - テスト実行による検証

2. Verification → Checklist Update
   - 完了状況の確認
   - チェックリストの更新

3. Checklist Update → Progress Tracking
   - 進捗状況の記録
   - 次のタスクの特定
```

## Validation & Constraints

### Business Rules

1. **ActionButtons状態制約**:
   - ローディング中はボタンクリック無効
   - エラー状態では適切なメッセージ表示
   - 無効化状態では視覚的フィードバック提供

2. **チェックリスト管理制約**:
   - 依存関係のある項目は順序実行
   - 完了日の自動記録
   - 検証方法の明示的記載

### Technical Constraints

1. **TypeScript型安全性**: すべてのインターフェースは厳密型チェック対応
2. **React Hook Rules**: useStateとuseEffectの適切な使用
3. **アクセシビリティ**: WCAG AA準拠のARIA属性設定
4. **パフォーマンス**: 既存動作時間の±5%以内維持

## Migration Strategy

既存のResultScreen実装からActionButtons分離への移行手順：

1. **Phase 1**: ActionButtonsコンポーネント作成（既存コードはそのまま）
2. **Phase 2**: 単体テスト作成と動作確認
3. **Phase 3**: ResultScreenでの統合とリファクタリング
4. **Phase 4**: 回帰テスト実行と性能検証
5. **Phase 5**: 旧実装の削除とクリーンアップ

この移行により、既存機能を破綻させることなく段階的な改善を実現します。

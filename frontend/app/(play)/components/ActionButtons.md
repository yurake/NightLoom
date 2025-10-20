# ActionButtons コンポーネントドキュメント

**更新日**: 2025-10-19  
**バージョン**: 1.0.0  
**実装ファイル**: [`ActionButtons.tsx`](ActionButtons.tsx)  
**テストファイル**: [`../../../tests/components/result/ActionButtons.test.tsx`](../../../tests/components/result/ActionButtons.test.tsx)

## 概要

ActionButtonsは結果画面で使用されるアクションボタンを管理するReactコンポーネントです。ユーザーが診断を再実行したり、エラー時にリトライしたりするための操作を提供します。WCAG AA準拠のアクセシビリティ機能と、堅牢な状態管理を備えています。

## 主な機能

- **再診断ボタン**: 診断フローを最初からやり直す
- **リトライボタン**: エラー発生時の再試行（オプショナル）
- **ローディング状態管理**: 非同期処理中の適切な状態表示
- **エラーハンドリング**: 操作エラーの表示と回復
- **アクセシビリティ**: WCAG AA準拠の完全実装
- **キーボード操作**: Enter/Spaceキー対応

## TypeScript インターフェース

```typescript
interface ActionButtonsProps {
  // 必須プロパティ
  onRestart: () => void | Promise<void>;
  
  // オプショナルプロパティ
  onRetry?: () => void | Promise<void>;
  isLoading?: boolean;
  isDisabled?: boolean;
  variant?: 'primary' | 'secondary';
  className?: string;
}
```

## 基本的な使用方法

### 最小構成（再診断のみ）
```typescript
import { ActionButtons } from '@/components/ActionButtons';

function ResultScreen() {
  const handleRestart = () => {
    window.location.href = '/';
  };

  return (
    <div>
      <ActionButtons onRestart={handleRestart} />
    </div>
  );
}
```

### 完全構成（リトライ機能付き）
```typescript
import { ActionButtons } from '@/components/ActionButtons';

function ResultScreen() {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleRestart = async () => {
    setIsLoading(true);
    try {
      await restartDiagnosis();
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    await retryLastAction();
  };

  return (
    <ActionButtons 
      onRestart={handleRestart}
      onRetry={handleRetry}
      isLoading={isLoading}
      variant="primary"
    />
  );
}
```

## プロパティ詳細

### onRestart (必須)
- **型**: `() => void | Promise<void>`
- **説明**: 診断を最初からやり直すときに呼び出されるコールバック
- **用途**: メイン画面への遷移、セッションリセット

### onRetry (オプショナル)
- **型**: `() => void | Promise<void>`
- **説明**: エラー時のリトライ処理コールバック
- **動作**: このプロパティが提供された場合のみリトライボタンが表示される

### isLoading (オプショナル)
- **型**: `boolean`
- **デフォルト**: `false`
- **説明**: ローディング状態を制御
- **効果**: `true`時にローディングインジケーター表示、ボタン無効化

### isDisabled (オプショナル)
- **型**: `boolean`
- **デフォルト**: `false`  
- **説明**: 全ボタンの無効化状態を制御
- **用途**: 特定の条件下でのユーザー操作制限

### variant (オプショナル)
- **型**: `'primary' | 'secondary'`
- **デフォルト**: `'primary'`
- **説明**: ボタンの視覚的スタイル
- **効果**: プライマリ（強調表示）またはセカンダリ（控えめ表示）

### className (オプショナル)
- **型**: `string`
- **説明**: 追加のCSSクラス
- **用途**: カスタムスタイリング、レイアウト調整

## 状態管理

### 内部状態
コンポーネントは以下の内部状態を管理します：

```typescript
interface InternalState {
  internalLoading: boolean;  // 内部ローディング状態
  error: string | null;      // エラーメッセージ
}
```

### ローディング状態の優先順位
1. 外部 `isLoading` prop（最優先）
2. 内部 `internalLoading` 状態
3. どちらか一方が `true` の場合、全体がローディング状態

### エラーハンドリング
- コールバック実行中の例外を自動キャッチ
- エラーメッセージをユーザーに表示
- `finally` ブロックで確実にローディング状態をクリア

## アクセシビリティ機能

### ARIA 属性
```typescript
// ボタン要素
aria-label="診断をもう一度実行します"
aria-disabled={isButtonDisabled ? 'true' : 'false'}
role="button"
tabIndex={isButtonDisabled ? -1 : 0}

// コンテナ要素
aria-busy={isLoading ? 'true' : 'false'}
```

### キーボード操作
- **Enter キー**: ボタン実行
- **Space キー**: ボタン実行  
- **Tab キー**: フォーカス移動
- 無効化時は `tabIndex="-1"` でフォーカス除外

### スクリーンリーダー対応
- 適切なセマンティック要素使用 (`<button>`)
- 説明的な `aria-label` 提供
- 状態変化の動的通知 (`aria-busy`, `aria-disabled`)

## パフォーマンス最適化

### useCallback の活用
```typescript
const handleRestartClick = useCallback(async () => {
  if (isButtonDisabled) return;
  
  setInternalState(prev => ({ ...prev, internalLoading: true, error: null }));
  
  try {
    await onRestart();
  } catch (error) {
    setInternalState(prev => ({ 
      ...prev, 
      error: error instanceof Error ? error.message : '操作に失敗しました' 
    }));
  } finally {
    setInternalState(prev => ({ ...prev, internalLoading: false }));
  }
}, [onRestart, isButtonDisabled]);
```

### 依存配列の最適化
- 必要最小限の依存関係のみ指定
- 不要な再レンダリングを防止
- メモリリークの防止

## エラーハンドリング

### 自動エラー回復
```typescript
try {
  await onRestart();
} catch (error) {
  // エラーを内部状態に保存
  // ユーザーフレンドリーなメッセージ表示
  // 操作可能状態の維持
} finally {
  // 確実なクリーンアップ
}
```

### エラーメッセージ表示
- `data-testid="error-message"` で識別可能
- ユーザーに分かりやすいメッセージ
- 操作継続が可能な設計

## テスト戦略

### テストカバレッジ
現在356行のテストケースで以下をカバー：

1. **基本レンダリング**: ボタン表示、プロパティ反映
2. **コールバック実行**: 同期・非同期処理の確認
3. **状態管理**: ローディング、エラー、無効化状態
4. **アクセシビリティ**: ARIA属性、キーボード操作
5. **エッジケース**: 例外処理、パフォーマンス

### テスト実行
```bash
# 単体テスト実行
pnpm test tests/components/result/ActionButtons.test.tsx

# カバレッジ付き実行
pnpm test --coverage tests/components/result/ActionButtons.test.tsx
```

## スタイリング

### Tailwind CSS クラス
```typescript
// コンテナ
"flex flex-col sm:flex-row gap-3 items-center justify-center"

// プライマリボタン  
"px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg"

// セカンダリボタン
"px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg"

// 無効化状態
"opacity-50 cursor-not-allowed"
```

### レスポンシブ対応
- **モバイル**: 縦並び (`flex-col`)
- **デスクトップ**: 横並び (`sm:flex-row`)
- **ギャップ**: `gap-3` で適切な間隔

## 関連コンポーネント

### 使用場所
- [`ResultScreen.tsx`](ResultScreen.tsx) - メインの使用場所
- [`ResultScreenWithMetrics.tsx`](ResultScreenWithMetrics.tsx) - パフォーマンス測定版

### 依存関係
- **React**: hooks (useState, useCallback)
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング

## 今後の拡張予定

### 機能拡張候補
1. **アニメーション**: ホバー・クリック効果の強化
2. **国際化**: 多言語対応（i18n）
3. **テーマ**: ダークモード対応
4. **分析**: ユーザー操作分析機能

### 保守性向上
1. **Storybook**: コンポーネントドキュメント
2. **Visual Testing**: 視覚回帰テスト
3. **Performance Budget**: パフォーマンス監視

---

**開発者向け注意事項**:
- プロパティ変更時はTypeScript型定義を先に更新
- 新機能追加時は対応するテストケースも追加
- アクセシビリティ要件は必須で遵守
- パフォーマンス劣化を防ぐため `useCallback` を適切に使用

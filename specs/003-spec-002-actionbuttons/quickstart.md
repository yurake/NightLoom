
# Quick Start Guide: spec 002未完了タスクの完了対応

**Date**: 2025-10-19  
**Feature**: ActionButtonsコンポーネント分離、チェックリスト完了確認
**Branch**: `003-spec-002-actionbuttons`

## Overview

この機能は既存のspec 002実装の品質向上を目的とし、ActionButtonsコンポーネント分離とチェックリスト完了確認を段階的に実施します。既存機能を破綻させることなく、TDD原則に従って安全にリファクタリングを行います。

## Prerequisites

### 環境要件
- Node.js 18+ 
- pnpm 8+
- TypeScript 5.0+
- Git

### 既存システム確認
```bash
# プロジェクトディレクトリに移動
cd /Users/yurak/git/NightLoom

# 現在のブランチ確認（003-spec-002-actionbuttonsにいることを確認）
git branch

# 依存関係の確認
cd frontend
pnpm install

# 既存テスト動作確認
pnpm test tests/components/result
pnpm exec playwright test results.spec.ts --reporter=list
```

## Quick Setup (5 minutes)

### Step 1: 環境初期化

```bash
# バックエンド起動（ターミナル1）
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド起動（ターミナル2）
cd frontend  
pnpm dev

# 動作確認
# - http://localhost:3000 でフロントエンド
# - http://localhost:8000/docs でバックエンドAPI
```

### Step 2: 現在の実装状況確認

```bash
# 既存ResultScreenの実装確認
cat frontend/app/\(play\)/components/ResultScreen.tsx | grep -n "もう一度診断する" -A 10 -B 2

# 現在のテスト状況確認
pnpm test tests/components/result --run

# spec 002チェックリスト状況確認
grep -c "\[ \]" specs/002-nightloom-kekka-gamen-hyoji/checklists/implementation-progress.md
```

### Step 3: 開発環境の検証

```bash
# TypeScriptコンパイル確認
cd frontend
pnpm type-check

# リント確認
pnpm lint

# 既存テスト実行
pnpm test -- --passWithNoTests

# E2E環境確認
pnpm exec playwright install
pnpm exec playwright test --config=playwright.config.ts --list
```

## Development Workflow

### Phase 1: ActionButtons コンポーネント分離 (35分)

#### 1.1 テスト先行作成（TDD）

```bash
# テストファイル作成
touch frontend/tests/components/result/ActionButtons.test.tsx

# テスト内容（失敗させるテスト）
cat << 'EOF' > frontend/tests/components/result/ActionButtons.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ActionButtons } from '@/app/(play)/components/ActionButtons';

describe('ActionButtons', () => {
  it('should render restart button', () => {
    const mockOnRestart = jest.fn();
    render(<ActionButtons onRestart={mockOnRestart} />);
    
    const restartButton = screen.getByTestId('restart-button');
    expect(restartButton).toBeInTheDocument();
    expect(restartButton).toHaveTextContent('もう一度診断する');
  });
  
  it('should call onRestart when clicked', () => {
    const mockOnRestart = jest.fn();
    render(<ActionButtons onRestart={mockOnRestart} />);
    
    const restartButton = screen.getByTestId('restart-button');
    fireEvent.click(restartButton);
    
    expect(mockOnRestart).toHaveBeenCalledTimes(1);
  });
});
EOF

# テスト実行（RED状態確認）
pnpm test ActionButtons.test.tsx
```

#### 1.2 ActionButtons コンポーネント実装

```bash
# コンポーネントファイル作成
touch frontend/app/\(play\)/components/ActionButtons.tsx

# 基本実装
cat << 'EOF' > frontend/app/\(play\)/components/ActionButtons.tsx
'use client';

import React, { useState } from 'react';
import type { ActionButtonsProps } from '@/types/result';

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onRestart,
  onRetry,
  isLoading = false,
  isDisabled = false,
  variant = 'primary',
  className = '',
}) => {
  const [internalLoading, setInternalLoading] = useState(false);

  const handleRestart = async () => {
    if (isLoading || isDisabled) return;
    
    try {
      setInternalLoading(true);
      await onRestart();
    } catch (error) {
      console.error('Restart error:', error);
    } finally {
      setInternalLoading(false);
    }
  };

  const isButtonDisabled = isLoading || isDisabled || internalLoading;

  return (
    <section className={`mt-8 pb-4 text-center xs:mt-10 sm:mt-12 ${className}`}>
      <button
        onClick={handleRestart}
        disabled={isButtonDisabled}
        data-testid="restart-button"
        className="w-full min-h-[44px] rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 active:bg-blue-800 xs:w-auto xs:px-8 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-describedby="restart-help"
      >
        {internalLoading ? '処理中...' : 'もう一度診断する'}
      </button>
      <div id="restart-help" className="sr-only">
        新しい診断セッションを開始します
      </div>
    </section>
  );
};
EOF

# 型定義追加
echo "export interface ActionButtonsProps {
  onRestart: () => void | Promise<void>;
  onRetry?: () => void | Promise<void>;
  isLoading?: boolean;
  isDisabled?: boolean;
  variant?: 'primary' | 'secondary';
  className?: string;
}" >> frontend/app/types/result.ts
```

#### 1.3 テスト確認（GREEN状態）

```bash
# テスト再実行（GREEN状態確認）
pnpm test ActionButtons.test.tsx

# 型チェック
pnpm type-check
```

#### 1.4 ResultScreen統合

```bash
# バックアップ作成
cp frontend/app/\(play\)/components/ResultScreen.tsx frontend/app/\(play\)/components/ResultScreen.tsx.backup

# ActionButtons統合（手動編集が推奨）
# 1. ActionButtonsをimport
# 2. 既存のbuttonセクション（230-241行目）を削除
# 3. ActionButtonsコンポーネントに置き換え

echo "
// ResultScreen.tsxに追加するimport
import { ActionButtons } from './ActionButtons';

// 既存のbuttonセクションを以下に置き換え
<ActionButtons
  onRestart={() => window.location.href = '/'}
  isLoading={isLoading}
  isDisabled={!!error}
/>
" > integration-guide.txt
```

### Phase 2: チェックリスト完了確認 (20分)

#### 3.1 実装状況の検証

```bash
# 各機能の動作確認スクリプト作成
cat << 'EOF' > verify-implementation.sh
#!/bin/bash
echo "=== Implementation Verification ==="

echo "1. ActionButtons component exists:"
ls -la frontend/app/\(play\)/components/ActionButtons.tsx

echo "2. Tests exist and pass:"
cd frontend && pnpm test ActionButtons.test.tsx --verbose

echo "3. E2E tests run successfully:"
pnpm exec playwright test results.spec.ts --reporter=line

echo "4. Type check passes:"
pnpm type-check

echo "5. Lint passes:"
pnpm lint

echo "=== Verification Complete ==="
EOF

chmod +x verify-implementation.sh
./verify-implementation.sh
```

#### 3.2 チェックリスト更新

```bash
# spec 002のチェックリスト更新（手動編集）
# 完了した項目に [x] マークを追加し、完了日を記録

echo "完了項目の例:
- [x] ActionButtons コンポーネント実装 (完了日: 2025-10-19)
- [x] 単体テスト作成 (完了日: 2025-10-19) 
- [x] E2Eテスト有効化 (完了日: 2025-10-19)" > checklist-updates.md
```

## Testing Strategy

### 単体テスト (Jest + Testing Library)

```bash
# 新しいテスト実行
pnpm test tests/components/result/ActionButtons.test.tsx

# カバレッジ確認
pnpm test -- --coverage --collectCoverageFrom="**/ActionButtons.tsx"

# 既存テストの回帰確認
pnpm test tests/components/result/
```

### E2Eテスト (Playwright)

```bash
# 結果画面フローテスト
pnpm exec playwright test results.spec.ts --headed --slowMo=1000

# アクセシビリティテスト
pnpm exec playwright test accessibility-keyboard.spec.ts

# 全テスト実行
pnpm exec playwright test --reporter=html
```

### パフォーマンステスト

```bash
# 既存動作時間の測定
pnpm exec playwright test results.spec.ts --grep "performance requirements"

# Lighthouse CI（オプション）
npx lhci autorun
```

## Debugging

### 一般的な問題と解決策

#### 1. TypeScript型エラー
```bash
# 型定義の確認
pnpm type-check

# 型ファイルの再生成
rm -rf node_modules/.cache
pnpm install
```

#### 2. テスト失敗
```bash
# デバッグモードでテスト実行
pnpm test ActionButtons.test.tsx --verbose --no-cache

# DOM構造の確認
screen.debug() # テストコードに追加
```

#### 3. E2Eテスト不安定性
```bash
# ヘッドフルモードで実行
pnpm exec playwright test results.spec.ts --headed --slowMo=500

# スクリーンショット確認
pnpm exec playwright test results.spec.ts --screenshot=on
```

#### 4. コンポーネント統合エラー
```bash
# 既存実装の復元
cp frontend/app/\(play\)/components/ResultScreen.tsx.backup frontend/app/\(play\)/components/ResultScreen.tsx

# 段階的統合
# 1. ActionButtonsをコメントアウトして統合
# 2. propsを一つずつ追加
# 3. 既存ボタンを削除
```

## Performance Monitoring

### 成功基準の測定

```bash
# 実装前後の性能比較
echo "Before:" > performance-log.txt
pnpm exec playwright test results.spec.ts --grep "performance requirements" >> performance-log.txt

# 実装後
echo "After:" >> performance-log.txt
pnpm exec playwright test results.spec.ts --grep "performance requirements" >> performance-log.txt

# 差分確認（±5%以内の要件）
```

### 継続的監視

```bash
# CI/CDでの自動テスト
pnpm test:ci
pnpm exec playwright test --reporter=github

# メトリクス収集
pnpm run build
pnpm run analyze # バンドルサイズ確認
```

## Quality Gates

実装完了前に以下をすべて通過する必要があります：

```bash
# 1. 全テスト通過
pnpm test && pnpm exec playwright test

# 2. 型チェック通過
pnpm type-check

# 3. リント通過
pnpm lint

# 4. ビルド成功
pnpm build

# 5. パフォーマンス基準達成
./verify-performance.sh

# 6. アクセシビリティ基準達成
pnpm exec playwright test accessibility-keyboard.spec.ts
```

## Rollback Plan

問題が発生した場合の復旧手順：

```bash
# 1. 既存実装に復元
cp frontend/app/\(play\)/components/ResultScreen.tsx.backup frontend/app/\(play\)/components/ResultScreen.tsx

# 2. ActionButtonsファイル削除
rm frontend/app/\(play\)/components/ActionButtons.tsx
rm frontend/tests/components/result/ActionButtons.test.tsx

# 3. E2Eテスト復元
cp frontend/e2e/results.spec.ts.backup frontend/e2e/results.spec.ts

# 4. 型定義復元
git checkout frontend/app/types/result.ts

# 5. 動作確認
pnpm test && pnpm exec playwright test results.spec.ts
```

## Next Steps

実装完了後の推奨アクション：

1. **PR作成**: 変更内容のレビューリクエスト
2. **ドキュメント更新**: README.mdとコンポーネントドキュメント更新
3. **メトリクス設定**: 継続的パフォーマンス監視の設定
4. **ユーザーテスト**: 実際の診断フローでの動作確認

## Related Documentation

- [Feature Spec](spec.md) - 機能仕様の詳細
- [Implementation Plan](plan.md) - 技術実装計画
- [Data Model](data-model.md) - データ構造とインターフェース
- [Type Definitions](contracts/action-buttons-types.ts) - TypeScript型定義
- [Original spec 002](../002-nightloom-kekka-gamen-hyoji/spec.md) - 元の結果画面仕様

---

**実装時間見積もり**: 合計 65分
- Phase 1 (ActionButtons分離): 30分
- Phase 2 (E2Eテスト有効化): 20分
- Phase 3 (チェックリスト完了): 15分

**前提**: 開発環境が既に構築済みであることを前提とします。

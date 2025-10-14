# Quickstart: NightLoom結果画面表示機能

**Feature**: NightLoom結果画面表示機能  
**Quickstart Date**: 2025-10-14  
**対象**: 開発者・テスター・レビュアー

## 概要

このクイックスタートガイドは、NightLoom結果画面表示機能の開発・テスト・デプロイを迅速に開始するための手順書です。

## 前提条件

### システム要件
- Node.js 18.0.0+
- pnpm 8.0.0+
- Git 2.30.0+

### 既存環境
- NightLoomプロジェクト（`/Users/yurak/git/NightLoom`）がセットアップ済み
- フロントエンド（Next.js 14）とバックエンド（FastAPI）が稼働可能
- テーマシステム（ThemeProvider）が実装済み

## セットアップ（5分）

### 1. リポジトリ準備

```bash
# プロジェクトルートに移動
cd /Users/yurak/git/NightLoom

# ブランチ作成・切り替え
git checkout -b 002-nightloom-kekka-gamen-hyoji

# 依存関係確認
cd frontend
pnpm install
```

### 2. 開発環境起動

```bash
# バックエンド起動（ターミナル1）
cd backend
uv run --extra dev uvicorn app.main:app --reload --port 8000

# フロントエンド起動（ターミナル2）
cd frontend
pnpm dev
```

### 3. 環境確認

ブラウザで以下を確認：
- http://localhost:3000 - フロントエンド
- http://localhost:8000/docs - バックエンドAPI（Swagger）

## 開発手順（TDD）

### Phase 1: コンポーネント基盤（30分）

#### 1.1 型定義作成

```bash
# 型定義ファイル作成
mkdir -p frontend/app/types
```

[`frontend/app/types/result.ts`](frontend/app/types/result.ts) を作成：

```typescript
// contracts/result-types.ts の内容をコピー
export * from '../../../specs/002-nightloom-kekka-gamen-hyoji/contracts/result-types';
```

#### 1.2 テストファイル作成

```bash
# テストディレクトリ作成
mkdir -p frontend/tests/components/result
```

[`frontend/tests/components/result/ResultScreen.test.tsx`](frontend/tests/components/result/ResultScreen.test.tsx):

```typescript
import { render, screen } from '@testing-library/react';
import { ResultScreen } from '@/app/(play)/components/ResultScreen';
import { mockResult2Axes } from '@/app/types/result';

describe('ResultScreen', () => {
  it('結果データを正しく表示する', () => {
    render(<ResultScreen result={mockResult2Axes} />);
    
    // タイプ名表示確認
    expect(screen.getByText('Logical Thinker')).toBeInTheDocument();
    
    // 軸スコア表示確認
    expect(screen.getByText('論理性')).toBeInTheDocument();
    expect(screen.getByText('75.5')).toBeInTheDocument();
  });
});
```

#### 1.3 コンポーネント基本実装

```bash
# コンポーネントディレクトリ作成
mkdir -p frontend/app/\(play\)/components
```

[`frontend/app/(play)/components/ResultScreen.tsx`](frontend/app/(play)/components/ResultScreen.tsx):

```typescript
interface ResultScreenProps {
  result: ResultData;
}

export const ResultScreen: React.FC<ResultScreenProps> = ({ result }) => {
  return (
    <div className="result-screen">
      <h1>{result.type.name}</h1>
      {/* 基本表示のみ */}
    </div>
  );
};
```

#### 1.4 テスト実行

```bash
cd frontend
pnpm test -- ResultScreen.test.tsx
```

### Phase 2: API統合（20分）

#### 2.1 APIクライアント実装

[`frontend/app/services/session-api.ts`](frontend/app/services/session-api.ts):

```typescript
import { ResultData, GetResultRequest } from '@/app/types/result';

export class SessionApiClient {
  constructor(private baseUrl: string) {}

  async getResult(sessionId: string): Promise<ResultData> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/result`
    );
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
}
```

#### 2.2 統合テスト

[`frontend/tests/services/session-api.test.ts`](frontend/tests/services/session-api.test.ts):

```typescript
import { SessionApiClient } from '@/app/services/session-api';

// MSWでAPI モック
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('SessionApiClient', () => {
  it('結果を正常取得する', async () => {
    const client = new SessionApiClient('http://localhost:8000');
    const result = await client.getResult('test-session-id');
    
    expect(result.sessionId).toBe('test-session-id');
  });
});
```

### Phase 3: アニメーション（15分）

#### 3.1 スコアバーアニメーション

[`frontend/app/(play)/components/AxisScoreItem.tsx`](frontend/app/(play)/components/AxisScoreItem.tsx):

```typescript
export const AxisScoreItem: React.FC<{ axis: AxisScore }> = ({ axis }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(axis.score);
    }, 100);
    return () => clearTimeout(timer);
  }, [axis.score]);

  return (
    <div className="axis-score-item">
      <div 
        className="axis-bar-fill"
        style={{ 
          width: `${animatedScore}%`,
          transition: 'width 1s ease-out'
        }}
      />
    </div>
  );
};
```

### Phase 4: E2Eテスト（10分）

[`frontend/e2e/result-screen.spec.ts`](frontend/e2e/result-screen.spec.ts):

```typescript
import { test, expect } from '@playwright/test';

test('結果画面フルフロー', async ({ page }) => {
  // セッション作成 → 結果画面遷移をテスト
  await page.goto('/result/test-session-id');
  
  // タイプカード表示確認
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  
  // スコアバーアニメーション確認
  const progressBar = page.locator('.axis-bar-fill').first();
  await expect(progressBar).toHaveCSS('width', /\d+%/);
});
```

## 検証チェックリスト

### 機能確認
- [ ] 結果データが正しく表示される
- [ ] スコアバーが1秒でアニメーションする
- [ ] 「もう一度診断する」ボタンで初期画面に戻る
- [ ] エラー状態が適切に表示される

### 非機能確認
- [ ] 360px幅でレスポンシブ表示される
- [ ] アクセシビリティ（スクリーンリーダー対応）
- [ ] 初回レンダリング < 500ms
- [ ] アニメーション精度 ±50ms

### テスト確認
```bash
# ユニットテスト
pnpm test

# E2Eテスト
pnpm exec playwright test

# 型チェック
pnpm type-check

# Lint
pnpm lint
```

## デバッグ・トラブルシューティング

### よくある問題

#### 1. API接続エラー
```bash
# バックエンド稼働確認
curl http://localhost:8000/api/sessions/test-id/result

# CORSエラーの場合
# backend/app/main.py でCORS設定確認
```

#### 2. アニメーション不具合
```css
/* CSS Transition確認 */
.axis-bar-fill {
  transition: width 1s ease-out;
  will-change: width; /* GPU加速 */
}
```

#### 3. TypeScriptエラー
```bash
# 型定義再確認
pnpm type-check --watch

# キャッシュクリア
rm -rf .next
pnpm dev
```

### デバッグツール

#### 1. React Developer Tools
- コンポーネント状態確認
- props/state トレース

#### 2. Performance タブ
- アニメーション性能測定
- レンダリング時間計測

#### 3. ログ出力
```typescript
// development環境でのみログ
if (process.env.NODE_ENV === 'development') {
  console.log('Result ', result);
}
```

## デプロイ準備

### 1. ビルド確認
```bash
cd frontend
pnpm build
pnpm start # プロダクションビルド確認
```

### 2. テスト実行
```bash
# 全テスト実行
pnpm test:ci
pnpm exec playwright test --reporter=html
```

### 3. 品質チェック
```bash
# パフォーマンス測定
pnpm audit
pnpm run lighthouse

# セキュリティチェック
pnpm audit --audit-level=moderate
```

## パフォーマンス最適化

### バンドルサイズ最適化
```bash
# バンドル分析
pnpm run analyze

# 不要import削除
pnpm run lint --fix
```

### 画像最適化
```bash
# 最適化確認
ls -la public/assets/
```

### キャッシュ戦略
```typescript
// next.config.mjs
const nextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react']
  }
};
```

## 次のステップ

### 短期（1週間以内）
1. 基本機能テスト完了
2. レスポンシブ対応
3. アクセシビリティ対応

### 中期（1ヶ月以内）
1. パフォーマンス最適化
2. エラーハンドリング強化
3. E2Eテスト拡充

### 長期（将来）
1. テーマシステム統合（FR-026）
2. 高度なアニメーション
3. 国際化対応

## サポート・ドキュメント

- [仕様書](spec.md)
- [設計書](data-model.md)
- [API契約](contracts/result-api.openapi.yaml)
- [研究結果](research.md)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

このガイドに従うことで、効率的に結果画面表示機能を開発できます。

# Research: NightLoom結果画面表示機能

**Feature**: NightLoom結果画面表示機能  
**Research Date**: 2025-10-14  
**研究範囲**: 技術選定・実装パターン・パフォーマンス最適化

## 技術スタック研究

### Next.js 14 App Router 最適化

**Decision**: Next.js 14 App Router + Server Components の活用  
**Rationale**: 
- 既存プロジェクト構成（`frontend/app/`）との整合性
- Server Components によるバンドルサイズ削減
- 動的ルーティング `/result/[sessionId]` 対応容易性
- Streaming SSR による初回表示高速化

**Alternatives considered**:
- Pages Router: レガシーパターンであり、パフォーマンス劣化
- Vite + React: 既存プロジェクト構造の大幅変更が必要

### 状態管理パターン

**Decision**: React Context + useReducer パターン  
**Rationale**:
- セッション内一時データに最適（永続化不要）
- 軽量で過度な複雑性回避
- テスト容易性（reducer 単体テスト可能）
- 既存 ThemeProvider パターンとの統一性

**Alternatives considered**:
- Redux Toolkit: オーバーエンジニアリング（小規模状態管理）
- Zustand: 外部依存追加の必要性低い
- useState のみ: 複数コンポーネント間での状態共有困難

### アニメーション実装

**Decision**: CSS Transition + setTimeout による制御  
**Rationale**:
- 1秒±50ms の精密制御が可能
- GPU加速による滑らかなアニメーション
- ライブラリ依存なし（バンドルサイズ最小化）
- `prefers-reduced-motion` 対応容易

**Alternatives considered**:
- Framer Motion: 高機能だが重量（~60KB）、要件過多
- React Spring: 物理ベースアニメーション不要
- Web Animations API: ブラウザ互換性問題

## データフロー設計研究

### API統合パターン

**Decision**: fetch + async/await + エラー境界パターン  
**Rationale**:
- Next.js標準、追加ライブラリ不要
- TypeScript型安全性確保
- エラーハンドリングの明示化
- キャッシュ制御の柔軟性

**Alternatives considered**:
- SWR: キャッシュ機能不要（セッション単発データ）
- TanStack Query: 複雑なデータ同期不要
- Axios: fetch標準で十分

### レスポンシブ実装

**Decision**: Tailwind CSS + Container Queries（将来対応準備）  
**Rationale**:
- 既存プロジェクトとの統一性（`tailwind.config.ts`）
- ユーティリティクラスによる開発効率
- JITモードでのバンドルサイズ最適化
- カスタムプロパティ（CSS Variables）との併用

**Alternatives considered**:
- CSS Modules: 既存構成変更コスト高
- styled-components: ランタイム CSS-in-JS のパフォーマンス影響
- Vanilla CSS: 保守性・スケーラビリティ課題

## パフォーマンス最適化研究

### バンドル最適化

**Decision**: Dynamic Imports + Code Splitting  
**Rationale**:
- 結果画面の初回表示遅延回避
- 非クリティカルコンポーネントの遅延読み込み
- Core Web Vitals（LCP < 2.5s）達成

**研究結果**:
```typescript
// 重いアニメーションライブラリは動的import
const LazyAnimatedChart = lazy(() => import('./AnimatedChart'));

// Critical Rendering Path 最適化
const ResultScreen = () => {
  return (
    <div className="result-screen">
      <TypeCard /> {/* 即座に表示 */}
      <Suspense fallback={<ChartSkeleton />}>
        <LazyAnimatedChart />
      </Suspense>
    </div>
  );
};
```

### メモリ管理

**Decision**: useCallback + useMemo + WeakMap パターン  
**Rationale**:
- 不要な再レンダリング回避
- 大きなオブジェクト（軸データ）の参照最適化
- セッション終了時の自動クリーンアップ

**実装パターン**:
```typescript
const ResultScreen = memo(({ sessionId }: ResultScreenProps) => {
  const memoizedAxes = useMemo(() => 
    processAxesData(rawAxes), [rawAxes]
  );
  
  const handleRetry = useCallback(() => {
    clearSessionData(sessionId);
    navigate('/');
  }, [sessionId]);
  
  return <div>...</div>;
});
```

### アクセシビリティ研究

**Decision**: WCAG 2.1 AA準拠 + aria-live による動的更新  
**Rationale**:
- スクリーンリーダー対応必須
- プログレスバーアニメーション中の状態通知
- キーボードナビゲーション完全対応

**実装方針**:
```typescript
<div 
  role="progressbar" 
  aria-label={`${axisName}: ${score}ポイント`}
  aria-valuenow={score}
  aria-valuemin={0}
  aria-valuemax={100}
>
  <div 
    className="progress-fill"
    style={{ width: `${score}%` }}
    aria-hidden="true"
  />
</div>
```

## テスト戦略研究

### Unit Testing

**Decision**: Jest + React Testing Library + MSW  
**Rationale**:
- 既存テスト環境との統一
- ユーザー中心のテスト設計
- API モック化による独立性確保

**テストケース設計**:
- コンポーネント描画テスト（props検証）
- アニメーション動作テスト（timing検証）
- エラー状態テスト（fallback表示）
- レスポンシブ表示テスト（breakpoint検証）

### E2E Testing

**Decision**: Playwright + 実際APIサーバーとの統合  
**Rationale**:
- フルユーザーフロー検証
- 実API応答でのデータ型検証
- マルチブラウザ・デバイス対応確認

## 技術的課題と解決策

### 課題1: 動的軸数（2-6軸）のレスポンシブ表示

**解決策**: CSS Grid + clamp() による適応的レイアウト
```css
.axes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: clamp(1rem, 2.5vw, 1.5rem);
}
```

### 課題2: スコアアニメーション精度（±50ms要件）

**解決策**: RequestAnimationFrame + Performance API
```typescript
const animateScore = useCallback((targetScore: number) => {
  const startTime = performance.now();
  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / 1000, 1);
    
    setAnimatedScore(targetScore * progress);
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };
  requestAnimationFrame(animate);
}, []);
```

### 課題3: タイプカード動的背景グラデーション

**解決策**: CSS カスタムプロパティ + テーマシステム統合
```typescript
const themeGradients = {
  serene: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  adventure: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  focus: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
};
```

## リスク軽減策

### 技術的リスク

1. **LLM API遅延**: Loading Skeleton + Timeout制御
2. **メモリリーク**: WeakMap + useEffect cleanup
3. **アニメーション性能**: GPU層分離 + will-change最適化

### UX リスク

1. **理解困難性**: 軸説明tooltip + 視覚的方向性表示
2. **操作迷い**: 明確CTA配置 + プログレッシブ開示
3. **モバイル操作性**: タッチターゲット44px以上確保

## 実装優先順位

### Phase 1: コア機能（P0）
1. ResultScreen基本構造
2. TypeCard表示機能
3. AxesScores基本レンダリング
4. API統合

### Phase 2: UX強化（P1）
1. スコアバーアニメーション
2. レスポンシブ対応
3. エラーハンドリング
4. アクセシビリティ

### Phase 3: 最適化（P2）
1. パフォーマンス最適化
2. テスト実装
3. エッジケース対応
4. 将来拡張準備

## 参考資料

- [Next.js 14 App Router Documentation](https://nextjs.org/docs/app)
- [React 18 Concurrent Features](https://react.dev/blog/2022/03/29/react-v18)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/)
- [Core Web Vitals](https://web.dev/vitals/)
- [既存プロジェクト構成](../../frontend/)

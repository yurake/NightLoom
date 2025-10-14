# NightLoom結果画面表示機能 - 曖昧性明確化結果

**実行日時**: 2025-10-14T21:57  
**対象仕様**: specs/002-nightloom-kekka-gamen-hyoji/spec.md  
**参照文書**: docs/requirements/overview.md, docs/design/overview.md, docs/design/frontend-result-screen.md, docs/design/scoring-and-typing.md

## 特定された曖昧領域と明確化

### 1. スコア表示の詳細仕様【高優先度】

#### 曖昧な点
- [`AxisScoreItem`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:120)コンポーネントでスコア数値とバーの同期タイミング
- 小数点表示精度（`axis.score.toFixed(1)`）の一貫性
- アニメーション中の中間値表示の可否

#### 明確化
```tsx
interface AxisScoreDisplaySpec {
  // スコア数値表示精度: 小数第1位で統一
  scoreFormat: number; // toFixed(1)
  
  // アニメーション仕様
  animationTiming: {
    delay: 100; // ms後に開始
    duration: 1000; // 1秒で完了
    easing: "ease-out";
    showIntermediateValues: false; // アニメーション中は最終値のみ表示
  };
  
  // バーと数値の同期
  syncBehavior: "simultaneous"; // バーと数値を同時にアニメーション
}
```

### 2. エラーハンドリングとフォールバック表示【高優先度】

#### 曖昧な点
- [`ErrorMessage`](docs/design/frontend-result-screen.md:43)コンポーネントの具体的な表示内容
- セッション無効時のユーザー誘導方法
- プリセットタイプ使用時のユーザーへの告知の要否

#### 明確化
```tsx
interface ErrorHandlingSpec {
  errorTypes: {
    SESSION_NOT_FOUND: {
      message: "セッションが見つかりません";
      action: "初期画面へ戻る";
      autoRedirect: true;
      redirectDelay: 3000; // 3秒後
    };
    SESSION_NOT_COMPLETED: {
      message: "診断が完了していません";
      action: "診断を続ける";
      redirectTo: "/scene/current";
    };
    TYPE_GEN_FAILED: {
      message: "結果を生成しています...";
      showPresetDisclaimer: false; // プリセット使用を隠す
      fallbackBehavior: "seamless";
    };
  };
}
```

### 3. レスポンシブ対応の具体的ブレークポイント【中優先度】

#### 曖昧な点
- [`@media (max-width: 767px)`](docs/design/frontend-result-screen.md:337)以外の中間ブレークポイント
- タブレット横向き時の表示調整
- 極小画面（320px）での表示保証

#### 明確化
```css
/* 明確化されたブレークポイント仕様 */
@media (max-width: 359px) {
  /* 極小スマートフォン: 320-359px */
  .result-screen { padding: 0.75rem; }
  .type-name { font-size: 1.25rem; }
}

@media (min-width: 360px) and (max-width: 767px) {
  /* 標準モバイル: 360-767px */
  /* 既存仕様通り */
}

@media (min-width: 768px) and (max-width: 1023px) {
  /* タブレット: 768-1023px */
  .result-screen { padding: 1.5rem; }
  .axis-score-item { display: grid; grid-template-columns: 1fr 1fr; }
}

@media (min-width: 1024px) {
  /* デスクトップ: 1024px以上 */
  .result-screen { max-width: 800px; }
}
```

### 4. アクセシビリティ要件の具体的実装指針【中優先度】

#### 曖昧な点
- [`UX-004`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:113)のスクリーンリーダー対応の詳細
- キーボードナビゲーションの Tab順序
- カラーコントラスト比の具体的な検証方法

#### 明確化
```tsx
interface AccessibilitySpec {
  ariaLabels: {
    axisScore: "評価軸 {axisName}: {score}点";
    progressBar: "{axisName}の進捗: {percentage}パーセント";
    typeCard: "診断結果: {typeName}タイプ";
  };
  
  keyboardNavigation: {
    tabOrder: ["type-card", "retry-button"];
    skipLinks: false; // 結果画面では不要
  };
  
  colorContrast: {
    textOnGradient: "4.5:1以上"; // WCAG AA準拠
    scoreText: "#1f2937"; // 十分なコントラスト確保
    verificationTool: "axe-core";
  };
}
```

### 5. 再診断機能の動作仕様【中優先度】

#### 曖昧な点
- [`handleRetry`](docs/design/frontend-result-screen.md:144)関数実行時のセッションクリーンアップ
- 前回結果データの残存期間
- 新規診断開始時の初期化範囲

#### 明確化
```tsx
interface RetryFunctionSpec {
  sessionCleanup: {
    clearCurrentSession: true;
    clearLocalStorage: true;
    resetThemeContext: true;
  };
  
  navigation: {
    target: "/"; // ルート画面
    replaceHistory: true; // 戻るボタンで結果画面に戻らせない
  };
  
  dataIsolation: {
    newSessionId: "auto-generated";
    previousDataAccess: false;
    isolationLevel: "complete";
  };
}
```

### 6. パフォーマンス指標の測定方法【低優先度】

#### 曖昧な点
- [`SC-001`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:89)「500ms以下」の計測開始・終了タイミング
- [`SC-002`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:90)アニメーション完了の判定方法

#### 明確化
```tsx
interface PerformanceMetricsSpec {
  renderingTime: {
    startPoint: "API response received";
    endPoint: "first contentful paint";
    measurement: "performance.mark()";
    target: "< 500ms";
  };
  
  animationCompletion: {
    detection: "transitionend event";
    tolerance: "±50ms";
    target: "1000ms";
    fallback: "timeout at 1200ms";
  };
}
```

### 7. テーマ制御の将来対応【低優先度】

#### 曖昧な点
- [`FR-026`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:229)次回開発時のテーマ適用範囲
- [`themeId`](docs/design/overview.md:212)プロパティの受け渡し方法

#### 明確化
```tsx
interface ThemeIntegrationSpec {
  currentImplementation: {
    themeSupport: false;
    fallbackTheme: "default";
    cssVariables: "--surface-bg, --accent, --font-family";
  };
  
  futureImplementation: {
    themeSource: "API response";
    propagation: "ThemeProvider context";
    scope: ["TypeCard", "AxisScoreItem", "ActionButtons"];
    fallbackBehavior: "graceful degradation";
  };
}
```

## 実装推奨事項

### 即座に対応すべき項目
1. **スコア表示仕様の統一化** - 数値フォーマットとアニメーション同期
2. **エラーハンドリング詳細化** - 各エラー状態での具体的UI動作
3. **アクセシビリティ属性追加** - ARIA ラベルとキーボード対応

### 開発フェーズで検討する項目  
1. **レスポンシブブレークポイント詳細化** - 中間サイズでの最適化
2. **パフォーマンス計測実装** - 実測値による要件検証
3. **再診断機能のデータ分離** - セッション間の完全独立性保証

### 将来拡張で対応する項目
1. **テーマ切替基盤整備** - CSS変数とContext基盤
2. **高度なアクセシビリティ** - WCAG AAA準拠検討

## 結論

主要な曖昧性は**スコア表示の詳細仕様**と**エラーハンドリング動作**に集中している。これらを明確化することで、実装時の判断迷いを大幅に削減でき、一貫した UX を提供可能になる。

特に [`AxisScoreItem`](specs/002-nightloom-kekka-gamen-hyoji/spec.md:120) コンポーネントのアニメーション同期と [`ErrorMessage`](docs/design/frontend-result-screen.md:43) の状態別表示は、ユーザー体験に直結するため優先的な明確化が必要である。

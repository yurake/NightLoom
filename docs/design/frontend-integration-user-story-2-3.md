
# User Story 2-3 フロントエンド統合設計

## 概要

User Story 2（4シーン選択体験）とUser Story 3（結果表示）のフロントエンド統合設計。既存コンポーネントとの統合、新規コンポーネント設計、UI/UX詳細を定義し、実装準備を完了させる。

**対象タスク**: T037-T041 (User Story 2), T047-T052 (User Story 3)
**実装対象**: frontend/app/(play)/components/ 内の新規・既存コンポーネント

## 1. User Story 2: 4シーン選択体験のフロントエンド

### 1.1 新規コンポーネント設計

#### Scene.tsx (T037)
**目的**: 各シーンの物語表示と選択肢を提供するメインコンポーネント

```typescript
// frontend/app/(play)/components/Scene.tsx
interface SceneProps {
  sceneIndex: number; // 1-4 (既存SessionContextに合わせる)
  scene: Scene; // 既存のScene型を使用 from app/types/session.ts
  isLoading?: boolean;
  disabled?: boolean;
  onChoiceSelect: (choiceId: string) => void;
}

interface SceneState {
  selectedChoiceId: string | null;
  isSubmitting: boolean;
}
```

**主要機能**:
- 既存SessionContextからのテーマ取得（useSessionTheme）
- 物語テキストの段落分け表示
- 選択肢コンポーネントとの統合
- アニメーション付きのコンテンツ表示
- エラー状態とローディング状態の管理

**レイアウト構造**:
```
┌─────────────────────────────────┐
│ <ProgressIndicator />           │ ← 既存SessionContextから進行状況取得
├─────────────────────────────────┤
│                                 │
│      <article> Narrative        │ ← scene.narrative をセマンティックに表示  
│        (テーマ適用スタイル)       │
│                                 │
├─────────────────────────────────┤
│  <ChoiceOptions                 │ ← scene.choices を渡す
│    choices={scene.choices}      │
│    onChoiceSelect={onChoiceSelect} />
└─────────────────────────────────┘
```

**統合ポイント**:
- 既存ThemeProviderとの連携（useTheme()フック）
- 既存SessionContextとの連携（useSessionProgress()フック）
- CSS in Tailwind with テーマトークン利用

#### ChoiceOptions.tsx (T038)
**目的**: 選択肢の表示とインタラクション管理

```typescript
// frontend/app/(play)/components/ChoiceOptions.tsx
interface ChoiceOptionsProps {
  choices: Choice[]; // 既存のChoice型 from app/types/session.ts
  onChoiceSelect: (choiceId: string) => void;
  disabled?: boolean;
  selectedChoiceId?: string | null;
}

interface ChoiceButtonState {
  isHovered: boolean;
  isFocused: boolean;
  isPressed: boolean;
}
```

**状態管理**:
- hover/focus/active状態のマイクロインタラクション
- 選択中のローディング状態表示
- キーボード選択インデックス（Arrow keys + Enter）
- 楽観的UI（Optimistic UI）対応

**視覚設計**:
- テーマカラーによるボタンスタイリング（adventure/focus/serene/fallback）
- Material Design リップルエフェクト
- アクセシブルなフォーカスインジケータ（2px outline）
- `prefers-reduced-motion`対応のアニメーション

#### ProgressIndicator.tsx (T039)
**目的**: 4シーンの進行状況を視覚的に表示

```typescript
// frontend/app/(play)/components/ProgressIndicator.tsx
interface ProgressIndicatorProps {
  currentSceneIndex: number; // 1-4
  completedScenes: number[]; // [1, 2] など完了済みシーン番号配列
  totalScenes: number; // 4固定
  theme: ThemeId; // 既存型 from app/theme/ThemeProvider.tsx
}
```

**表示形式**:
- ドット形式の進行インジケータ（4ドット）
- 現在位置の強調表示（テーマカラー＋スケールアップ）  
- 完了済みシーンの視覚的確認（チェックマーク）
- `prefers-reduced-motion`対応のプログレッシブディスクロージャー

**アクセシビリティ**:
```tsx
<div 
  role="progressbar" 
  aria-valuenow={currentSceneIndex} 
  aria-valuemin={1} 
  aria-valuemax={totalScenes}
  aria-label={`進行状況: ${completedScenes.length}/${totalScenes}シーン完了`}
>
```

### 1.2 既存コンポーネント統合設計

#### SessionContext.tsx 拡張 (T040統合)

既存SessionContextは既に適切な状態管理を持っているため、**フック追加による機能拡張**を行う：

```typescript
// frontend/app/state/SessionContext.tsx への追加
// 既存コードは保持し、以下のヘルパーフックを追加

export function useSceneNavigation(): {
  canNavigateToScene: (sceneIndex: number) => boolean;
  isSceneAccessible: (sceneIndex: number) => boolean;
  getNextSceneIndex: () => number | null;
} {
  const { state } = useSession();
  
  return {
    canNavigateToScene: (sceneIndex: number) => 
      sceneIndex <= state.completedScenes.length + 1 && sceneIndex >= 1,
    isSceneAccessible: (sceneIndex: number) =>
      state.completedScenes.includes(sceneIndex) || sceneIndex === state.currentSceneIndex,
    getNextSceneIndex: () => 
      state.currentSceneIndex < 4 ? state.currentSceneIndex + 1 : null,
  };
}

export function useChoiceHistory(): {
  choices: ChoiceRecord[];
  addChoice: (sceneIndex: number, choiceId: string) => void;
  getChoiceForScene: (sceneIndex: number) => ChoiceRecord | undefined;
} {
  const { state, dispatch } = useSession();
  
  return {
    choices: state.session?.choices || [],
    addChoice: (sceneIndex: number, choiceId: string) => {
      // choiceSubmittedアクションでchoice履歴を記録
      // 既存のCHOICE_SUBMITTEDアクションを利用
    },
    getChoiceForScene: (sceneIndex: number) => 
      state.session?.choices.find(choice => choice.sceneIndex === sceneIndex),
  };
}
```

**変更点**:
- 既存reducerとactionは**変更なし**
- セレクター関数（useSessionProgress等）は**既存のまま利用**
- 新規ヘルパーフック追加のみ

#### sessionClient.ts API統合 (T040統合)

既存sessionClient.tsは既に適切なAPI呼び出しメソッドを持っているため、**利用方法の標準化**を行う：

```typescript
// frontend/app/services/sessionClient.ts
// 既存のgetScene, submitChoiceメソッドを活用

// 新規追加: カスタムフック for Scene遷移
export function useSceneApi() {
  const { state, dispatch } = useSession();
  const sessionId = useSessionId();
  
  const loadScene = async (sceneIndex: number) => {
    if (!sessionId) throw new SessionAPIError('Session not found');
    
    try {
      dispatch(sessionActions.setLoading(true));
      const response = await sessionClient.getScene(sessionId, sceneIndex);
      dispatch(sessionActions.loadScene(response.scene, sceneIndex));
    } catch (error) {
      dispatch(sessionActions.setError(error.message));
      throw error;
    }
  };
  
  const submitChoice = async (sceneIndex: number, choiceId: string) => {
    if (!sessionId) throw new SessionAPIError('Session not found');
    
    try {
      dispatch(sessionActions.setLoading(true));
      const response = await sessionClient.submitChoice(sessionId, sceneIndex, choiceId);
      
      // 楽観的更新: 即座にchoiceを記録
      dispatch(sessionActions.choiceSubmitted(sceneIndex, choiceId, response.nextScene));
      
      // 次シーンの存在確認と取得
      if (response.nextScene) {
        await loadScene(response.nextScene.sceneIndex);
      }
    } catch (error) {
      dispatch(sessionActions.setError(error.message));
      throw error;
    }
  };
  
  return { loadScene, submitChoice };
}
```

## 2. User Story 3: 結果表示統合設計

### 2.1 既存コンポーネント統合

#### ResultScreen.tsx 統合 (T047-T048)
**既存の`ResultScreen.tsx`を拡張**し、4シーン完了後の統合を実現

```typescript
// frontend/app/(play)/components/ResultScreen.tsx への統合
interface ResultScreenProps {
  // 既存のprops保持
  sessionId: string;
  apiClient: ApiClient;
  
  // 新規追加props（オプション）
  sceneChoices?: SceneChoice[]; // 4シーンでの選択履歴
  onRestartDiagnosis?: () => void;
  showChoiceHistory?: boolean; // 選択履歴表示フラグ
}

interface SceneChoice {
  sceneIndex: number;
  narrative: string;
  chosenOption: Choice;
  timestamp: string;
}
```

**統合要素**:
- 選択履歴の表示（折りたたみ式、オプション）
- 再診断ボタンの統合（ActionButtonsコンポーネント更新）
- 結果画面でのテーマ継続適用（SessionContextからtheme取得）

**レイアウト統合**:
```
┌─────────────────────────────────┐
│    [TypeCard] (既存)            │ ← テーマ適用
├─────────────────────────────────┤  
│    [AxesScores] (既存)          │
├─────────────────────────────────┤
│  [ChoiceHistorySummary] (新規)   │ ← 4シーンの選択サマリ（折りたたみ式）
├─────────────────────────────────┤
│  診断情報 (既存)                 │
├─────────────────────────────────┤
│  [RestartDiagnosis] (新規)      │ ← ActionButtons拡張
└─────────────────────────────────┘
```

### 2.2 新規機能コンポーネント

#### RestartDiagnosis.tsx (T051)
**目的**: 診断完了後の再開始機能

```typescript
// frontend/app/(play)/components/RestartDiagnosis.tsx
interface RestartDiagnosisProps {
  onRestart: () => void;
  theme: ThemeId;
  isRestarting?: boolean;
}

interface RestartConfirmationState {
  showConfirmation: boolean;
  isProcessing: boolean;
}
```

**機能詳細**:
- セッション状態のクリーンアップ（SessionContext.resetSession）
- `localStorage`からの診断状態削除
- ホームページ（`/`）への遷移
- 確認ダイアログ（診断進行中の場合）

**統合処理**:
```tsx
const handleRestart = async () => {
  // 1. SessionContext状態リセット
  dispatch(sessionActions.resetSession());
  
  // 2. localStorage クリーンアップ  
  localStorage.removeItem('nightloom-session');
  localStorage.removeItem('nightloom-progress');
  
  // 3. ナビゲーション
  router.push('/');
};
```

#### ChoiceHistorySummary.tsx (新規、T048拡張)
**目的**: 4シーンでの選択履歴のサマリ表示

```typescript
// frontend/app/(play)/components/ChoiceHistorySummary.tsx
interface ChoiceHistorySummaryProps {
  choices: SceneChoice[];
  theme: ThemeId;
  isExpanded?: boolean;
}
```

**表示内容**:
- シーン別選択肢の簡易サマリ
- 折りたたみ式詳細表示
- 選択した理由の振り返り（将来拡張）

## 3. 統合フロー設計

### 3.1 ナビゲーションフロー

```
Home (/) 
  ↓ keyword入力 + bootstrap
Scene 1 (/scene/1) 
  ↓ choice選択 + API呼び出し
Scene 2 (/scene/2)
  ↓ choice選択 + API呼び出し  
Scene 3 (/scene/3)
  ↓ choice選択 + API呼び出し
Scene 4 (/scene/4)
  ↓ choice選択 + result API呼び出し
Result (/result)
  ↓ 再診断 or 終了
```

**URL設計**:
- `/scene/[sceneIndex]` - 動的ルーティング（App Router）
- `/result` - 結果表示（既存）
- クエリパラメータでの状態復元: `/scene/2?session=abc123`

**ルーティング実装**:
```typescript
// frontend/app/(play)/scene/[sceneIndex]/page.tsx
export default function ScenePage({ params }: { params: { sceneIndex: string } }) {
  const sceneIndex = parseInt(params.sceneIndex);
  const { state } = useSession();
  const { loadScene, submitChoice } = useSceneApi();


  
  const handleChoiceSelect = async (choiceId: string) => {
    await submitChoice(sceneIndex, choiceId);
  };

  return (
    <Scene 
      sceneIndex={sceneIndex}
      scene={state.currentScene}
      isLoading={state.isLoading}
      onChoiceSelect={handleChoiceSelect}
    />
  );
}
```

### 3.2 状態管理フロー

**SessionContext状態変化**:
```
1. keyword → theme決定 → bootstrap → session作成
2. sceneIndex=1 → Scene 1表示 → choice選択
3. choice選択 → choiceHistory追加 → sceneIndex++ → 次シーン表示
4. 全4シーン完了 → canProceedToResult=true → result API呼び出し
5. 結果表示 → 再診断でセッション完全リセット
```

**エラー回復フロー**:
```
API失敗 → SessionContext.error設定 → エラー表示コンポーネント → リトライボタン
セッション期限切れ → 新規セッション開始案内 → ホームページリダイレクト  
不正シーンアクセス → 適切なシーンへリダイレクト → 進行状況復元
ネットワーク断 → オフラインUI表示 → 復旧時の自動再開
```

### 3.3 永続化戦略

**localStorage設計**:
```typescript
interface PersistedSessionState {
  sessionId: string;
  currentSceneIndex: number;
  completedScenes: number[];
  selectedKeyword: string;
  theme: ThemeId;
  timestamp: string;
}

// 保存キー: 'nightloom-session-state'
// 有効期限: 24時間（診断セッションの想定完了時間）
```

**状態復元ロジック**:
```typescript
export function useSessionPersistence() {
  const { state, dispatch } = useSession();
  
  useEffect(() => {
    // ページロード時の状態復元
    const saved = localStorage.getItem('nightloom-session-state');
    if (saved) {
      const parsed: PersistedSessionState = JSON.parse(saved);
      if (isValidSession(parsed)) {
        dispatch(sessionActions.restoreSession(parsed));
      }
    }
  }, []);
  
  useEffect(() => {
    // 状態変化時の自動保存
    if (state.session) {
      const toSave: PersistedSessionState = {
        sessionId: state.session.id,
        currentSceneIndex: state.currentSceneIndex,
        completedScenes: state.completedScenes,
        selectedKeyword: state.session.selectedKeyword!,
        theme: state.session.themeId,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('nightloom-session-state', JSON.stringify(toSave));
    }
  }, [state.session, state.currentSceneIndex, state.completedScenes]);
}
```

## 4. UI/UX詳細設計

### 4.1 レスポンシブ設計

**ブレークポイント設計**:
```typescript
// Tailwind CSS breakpoints
const breakpoints = {
  sm: '640px',  // モバイル横向き
  md: '768px',  // タブレット縦
  lg: '1024px', // タブレット横・小型デスクトップ  
  xl: '1280px', // デスクトップ
};
```

**レイアウト適応**:
- **360px-639px** (モバイル縦): シングルカラム、フルハイト、大きなタッチターゲット
- **640px-767px** (モバイル横): 2カラム選択肢、進行表示をヘッダー固定
- **768px-1023px** (タブレット): 中央寄せ、最大幅制限、サイドマージン
- **1024px+** (デスクトップ): 左右マージン、視線誘導、ホバー効果

### 4.2 アニメーション設計

**遷移アニメーション**:
```css
/* シーン切り替え */
.scene-enter {
  opacity: 0;
  transform: translateY(20px);
}
.scene-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 300ms ease-out, transform 300ms ease-out;
}

/* 選択肢ホバー */
.choice-button {
  transition: all 150ms ease-out;
}
.choice-button:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* 進行状況更新 */
.progress-dot {
  transition: all 500ms cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-dot.completed {
  transform: scale(1.1);
  background: var(--color-accent);
}
```

**reduced-motion対応**:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .choice-button:hover {
    transform: none; /* スケール無効化 */
  }
}
```

### 4.3 テーマ統合詳細

**テーマ別コンポーネント適応**:
```typescript
// 各テーマでのビジュアル差別化
const themeStyleMap = {
  adventure: {
    sceneBackground: 'bg-gradient-to-br from-slate-800 to-orange-900',
    choiceButton: 'bg-orange-500 hover:bg-orange-600 text-amber-50',
    progressDot: 'bg-orange-400',
    narrative: 'text-amber-50 font-serif leading-relaxed',
  },
  focus: {
    sceneBackground: 'bg-gradient-to-br from-blue-900 to-indigo-800',
    choiceButton: 'bg-blue-500 hover:bg-blue-600 text-blue-50',
    progressDot: 'bg-blue-400',
    narrative: 'text-blue-50 font-sans leading-normal',
  },
  serene: {
    sceneBackground: 'bg-gradient-to-br from-green-800 to-emerald-700',
    choiceButton: 'bg-green-500 hover:bg-green-600 text-green-50',
    progressDot: 'bg-green-400',
    narrative: 'text-green-50 font-light leading-loose',
  },
  fallback: {
    sceneBackground: 'bg-gradient-to-br from-gray-700 to-gray-800',
    choiceButton: 'bg-gray-500 hover:bg-gray-600 text-gray-50',
    progressDot: 'bg-gray-400',
    narrative: 'text-gray-50 font-normal leading-normal',
  },
} as const;

// コンポーネント内での使用例
export function Scene({ scene, theme, ...props }: SceneProps) {
  const styles = themeStyleMap[theme] || themeStyleMap.fallback;
  
  return (
    <div className={`scene-container ${styles.sceneBackground}`}>
      <article className={`narrative ${styles.narrative}`}>
        {scene.narrative}
      </article>
      {/* ... */}
    </div>
  );
}
```

## 5. アクセシビリティ設計（WCAG 2.1 AA準拠）

### 5.1 セマンティックHTML構造

```tsx
// Scene.tsx のセマンティック構造
export function Scene({ scene, sceneIndex, onChoiceSelect }: SceneProps) {
  return (
    <main role="main" aria-labelledby="scene-title">
      <header className="scene-header">
        <h1 id="scene-title">シーン {sceneIndex}</h1>
        <ProgressIndicator 
          currentSceneIndex={sceneIndex} 
          aria-label={`進行状況: シーン${sceneIndex}/4`}
        />
      </header>
      
      <section aria-labelledby="narrative-heading">
        <h2 id="narrative-heading" className="sr-only">物語</h2>
        <article 
          className="narrative"
          aria-live="polite" 
          aria-atomic="true"
        >
          {scene.narrative}
        </article>
      </section>
      
      <section aria-labelledby="choices-heading">
        <h2 id="choices-heading" className="sr-only">選択肢</h2>
        <ChoiceOptions 
          choices={scene.choices}
          onChoiceSelect={onChoiceSelect}
          aria-describedby="choice-instructions"
        />
        <p id="choice-instructions" className="sr-only">
          矢印キーで選択肢を移動、Enterで決定できます
        </p>
      </section>
    </main>
  );
}
```

### 5.2 キーボードナビゲーション

```typescript
// ChoiceOptions.tsx のキーボード対応
export function ChoiceOptions({ choices, onChoiceSelect }: ChoiceOptionsProps) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  
  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex(prev => Math.min(prev + 1, choices.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
      case ' ': // Space key
        event.preventDefault();
        onChoiceSelect(choices[focusedIndex].id);
        break;
      case 'Home':
        event.preventDefault();
        setFocusedIndex(0);
        break;
      case 'End':
        event.preventDefault();
        setFocusedIndex(choices.length - 1);
        break;
    }
  };
  
  return (
    <div 
      role="group"
      aria-labelledby="choices-heading"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {choices.map((choice, index) => (
        <button
          key={choice.id}
          className={`choice-button ${index === focusedIndex ? 'focused' : ''}`}
          onClick={() => onChoiceSelect(choice.id)}
          tabIndex={-1} // グループ内フォーカス管理
          aria-describedby={`choice-desc-${choice.id}`}
        >
          {choice.text}
          <span id={`choice-desc-${choice.id}`} className="sr-only">
            選択肢 {index + 1} / {choices.length}
          </span>
        </button>
      ))}
    </div>
  );
}
```

### 5.3 スクリーンリーダー対応

**動的コンテンツ通知**:
```tsx
// 進行状況やシーン変更の音声通知
export function LiveRegion() {
  const { state } = useSession();
  const [announcement, setAnnouncement] = useState('');
  
  useEffect(() => {
    if (state.currentSceneIndex > 0) {
      setAnnouncement(`シーン${state.currentSceneIndex}に移動しました。`);
    }
  }, [state.currentSceneIndex]);
  
  useEffect(() => {
    if (state.completedScenes.length > 0) {
      const completed = state.completedScenes.length;
      setAnnouncement(`${completed}シーン完了。残り${4 - completed}シーンです。`);
    }
  }, [state.completedScenes]);
  
  return (
    <div 
      aria-live="assertive" 
      aria-atomic="true" 
      className="sr-only"
    >
      {announcement}
    </div>
  );
}
```

## 6. パフォーマンス最適化設計

### 6.1 コード分割戦略

```typescript
// 遅延読み込み設計
import { lazy, Suspense } from 'react';

// シーンコンポーネントの動的インポート
const Scene = lazy(() => import('../components/Scene'));
const ResultScreen = lazy(() => import('../components/ResultScreen'));

// ページレベルでのSuspense適用
export default function ScenePage({ params }: ScenePageProps) {
  return (
    <Suspense fallback={<SceneLoadingSkeleton />}>
      <Scene sceneIndex={parseInt(params.sceneIndex)} />
    </Suspense>
  );
}

// バンドル分析用のコメント
/* webpackChunkName: "scene-components" */ '../components/Scene'
/* webpackChunkName: "result-components" */ '../components/ResultScreen'
```

### 6.2 データキャッシュ戦略

```typescript
// sessionClient.ts にキャッシュ機能追加
export class SessionClient {
  private sceneCache = new Map<string, Scene>();
  private cacheTimeout = 5 * 60 * 1000; // 5分

  async getScene(sessionId: string, sceneIndex: number): Promise<SceneResponse> {
    const cacheKey = `${sessionId}:scene:${sceneIndex}`;
    
    // キャッシュ確認
    if (this.sceneCache.has(cacheKey)) {
      const cached = this.sceneCache.get(cacheKey)!;
      return { sessionId, scene: cached };
    }
    
    // API呼び出し
    const response = await this.getSceneFromAPI(sessionId, sceneIndex);
    
    // キャッシュ保存
    this.sceneCache.set(cacheKey, response.scene);
    setTimeout(() => {
      this.sceneCache.delete(cacheKey);
    }, this.cacheTimeout);
    
    return response;
  }
}
```

### 6.3 画像・アセット最適化

```typescript
// 画像の遅延読み込み設計
interface OptimizedImageProps {
  src: string;
  alt: string;

  theme: ThemeId;
  priority?: 'high' | 'medium' | 'low';
}

export function OptimizedImage({ src, alt, theme, priority = 'medium' }: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);
  
  return (
    <div className="image-container">
      {!isLoaded && !error && (
        <div className="image-skeleton bg-gray-200 animate-pulse" />
      )}
      <img 
        src={src} 
        alt={alt}
        loading={priority === 'high' ? 'eager' : 'lazy'}
        onLoad={() => setIsLoaded(true)}
        onError={() => setError(true)}
        className={`transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
      />
    </div>
  );
}
```

## 7. エラーハンドリング統合設計

### 7.1 エラー境界コンポーネント

```typescript
// frontend/app/utils/error-boundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class SceneErrorBoundary extends Component<PropsWithChildren, ErrorBoundaryState> {
  constructor(props: PropsWithChildren) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Scene Error Boundary caught an error:', error, errorInfo);
    
    // エラー報告（将来の分析用）
    if (typeof window !== 'undefined') {
      // エラートラッキングサービスへの送信（実装時に追加）
      console.log('Error details:', {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>問題が発生しました</h2>
          <details>
            <summary>エラー詳細</summary>
            <pre>{this.state.error?.message}</pre>
          </details>
          <button onClick={() => this.setState({ hasError: false })}>
            再試行
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 7.2 API エラーハンドリング統合

```typescript
// frontend/app/utils/error-handler.ts への統合
export function handleSceneAPIError(error: SessionAPIError, sceneIndex: number) {
  switch (error.code) {
    case 'SESSION_NOT_FOUND':
      // セッション復旧処理
      return {
        action: 'REDIRECT_HOME',
        message: 'セッションが見つかりません。最初からやり直してください。',
        severity: 'error'
      };
    
    case 'INVALID_SCENE_ACCESS':
      // 適切なシーンへリダイレクト
      return {
        action: 'REDIRECT_VALID_SCENE',
        message: `シーン${sceneIndex}にアクセスできません。`,
        severity: 'warning'
      };
    
    case 'NETWORK_ERROR':
      // リトライ可能エラー
      return {
        action: 'SHOW_RETRY',
        message: 'ネットワークエラーが発生しました。再試行してください。',
        severity: 'warning'
      };
    
    default:
      return {
        action: 'SHOW_GENERIC_ERROR',
        message: 'エラーが発生しました。しばらく待ってから再試行してください。',
        severity: 'error'
      };
  }
}
```

## 8. テスト戦略統合

### 8.1 コンポーネント単体テスト

```typescript
// frontend/tests/components/Scene.test.tsx
describe('Scene Component', () => {
  const mockScene: Scene = {
    sceneIndex: 1,
    themeId: 'adventure',
    narrative: 'テストシナリオ',
    choices: [
      { id: 'choice1', text: '選択肢1', weights: {} },
      { id: 'choice2', text: '選択肢2', weights: {} }
    ]
  };

  it('renders scene with narrative and choices', () => {
    const onChoiceSelect = jest.fn();
    
    render(
      <SessionProvider>
        <ThemeProvider>
          <Scene 
            sceneIndex={1}
            scene={mockScene}
            onChoiceSelect={onChoiceSelect}
          />
        </ThemeProvider>
      </SessionProvider>
    );

    expect(screen.getByText('テストシナリオ')).toBeInTheDocument();
    expect(screen.getByText('選択肢1')).toBeInTheDocument();
    expect(screen.getByText('選択肢2')).toBeInTheDocument();
  });

  it('calls onChoiceSelect when choice is clicked', async () => {
    const onChoiceSelect = jest.fn();
    
    render(
      <SessionProvider>
        <ThemeProvider>
          <Scene 
            sceneIndex={1}
            scene={mockScene}
            onChoiceSelect={onChoiceSelect}
          />
        </ThemeProvider>
      </SessionProvider>
    );

    await user.click(screen.getByText('選択肢1'));
    expect(onChoiceSelect).toHaveBeenCalledWith('choice1');
  });

  it('supports keyboard navigation', async () => {
    const onChoiceSelect = jest.fn();
    
    render(
      <SessionProvider>
        <ThemeProvider>
          <Scene 
            sceneIndex={1}
            scene={mockScene}
            onChoiceSelect={onChoiceSelect}
          />
        </ThemeProvider>
      </SessionProvider>
    );

    const choicesContainer = screen.getByRole('group');
    choicesContainer.focus();

    await user.keyboard('{ArrowDown}');
    await user.keyboard('{Enter}');

    expect(onChoiceSelect).toHaveBeenCalledWith('choice2');
  });
});
```

### 8.2 統合テスト

```typescript
// frontend/tests/integration/scene-flow.test.tsx
describe('Scene Flow Integration', () => {
  it('completes full 4-scene flow', async () => {
    const { container } = render(
      <SessionProvider>
        <ThemeProvider>
          <SceneFlowTestComponent />
        </ThemeProvider>
      </SessionProvider>
    );

    // シーン1開始
    expect(screen.getByText(/シーン 1/)).toBeInTheDocument();
    
    // 選択肢選択
    await user.click(screen.getByTestId('choice-button-0'));
    
    // シーン2遷移確認
    await waitFor(() => {
      expect(screen.getByText(/シーン 2/)).toBeInTheDocument();
    });

    // 進行状況確認
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '2');

    // 残りシーンでの同様の処理...
  });
});
```

## 9. 実装チェックリスト

### 9.1 User Story 2 実装要件

**新規コンポーネント (T037-T039)**:
- [ ] Scene.tsx: 物語表示とテーマ適応
- [ ] ChoiceOptions.tsx: 選択肢インタラクションとキーボード対応
- [ ] ProgressIndicator.tsx: 進行状況表示とアクセシビリティ

**統合要件 (T040-T041)**:
- [ ] SessionContext拡張フック実装
- [ ] sessionClient統合フック実装
- [ ] エラーハンドリング統合
- [ ] ページルーティング実装

### 9.2 User Story 3 実装要件

**結果画面統合 (T047-T052)**:
- [ ] ResultScreen.tsx 4シーン対応拡張
- [ ] RestartDiagnosis.tsx 実装
- [ ] ChoiceHistorySummary.tsx 実装
- [ ] 結果画面でのテーマ継続適用

### 9.3 横断的要件

**アクセシビリティ**:
- [ ] WCAG 2.1 AA準拠の実装
- [ ] キーボードナビゲーション完全対応
- [ ] スクリーンリーダー対応
- [ ] 適切なARIA属性の設定

**パフォーマンス**:
- [ ] コード分割実装
- [ ] 画像・アセット最適化
- [ ] API応答キャッシュ実装
- [ ] バンドルサイズ最適化

**テスト**:
- [ ] 全コンポーネントの単体テスト
- [ ] シーンフローの統合テスト
- [ ] E2Eテストでの全体検証
- [ ] アクセシビリティテスト

## 10. 技術仕様サマリ

### 10.1 コンポーネント構成

**新規追加**:
```
frontend/app/(play)/components/
├── Scene.tsx                    (T037)
├── ChoiceOptions.tsx           (T038) 
├── ProgressIndicator.tsx       (T039)
├── RestartDiagnosis.tsx        (T051)
└── ChoiceHistorySummary.tsx    (新規)
```

**既存拡張**:
```
frontend/app/(play)/components/
└── ResultScreen.tsx            (T047-T048統合)

frontend/app/state/
└── SessionContext.tsx          (T040ヘルパーフック追加)

frontend/app/services/
└── sessionClient.ts            (T040統合フック追加)
```

### 10.2 依存関係

**必須依存**:
- 既存SessionContext
- 既存ThemeProvider  
- 既存sessionClient
- 既存型定義 (session.ts, result.ts)

**新規依存**:
- なし（既存技術スタックで完全実装可能）

### 10.3 パフォーマンス指標

**目標値**:
- シーン遷移: <300ms
- 初回レンダリング: <1s
- バンドルサイズ: メインチャンク<200KB
- Lighthouse Score: >90

**計測ポイント**:
- LCP (Largest Contentful Paint)
- FID (First Input Delay)  
- CLS (Cumulative Layout Shift)

---

## 11. 完成基準

### 11.1 受入基準

**機能要件**:
- [ ] 4シーン完走が可能
- [ ] 各シーンでの選択肢選択が動作
- [ ] 進行状況が正確に表示
- [ ] 結果画面への遷移が動作
- [ ] 再診断機能が動作

**非機能要件**:
- [ ] モバイル(360px+)での正常表示
- [ ] キーボードのみでの操作可能
- [ ] スクリーンリーダーでの利用可能
- [ ] 目標パフォーマンス達成

### 11.2 品質保証

**テストカバレッジ**:
- 単体テスト: 90%+
- 統合テスト: 主要フロー100%
- E2Eテスト: ユーザーストーリー100%

**ブラウザ対応**:
- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

---

**設計完了**: User Story 2-3のフロントエンド統合設計が完了しました。実装チームは本設計書に基づいて、段階的な実装を進めることができます。

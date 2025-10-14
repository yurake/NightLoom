# Data Model: NightLoom結果画面表示機能

**Feature**: NightLoom結果画面表示機能  
**Model Date**: 2025-10-14  
**モデル範囲**: フロントエンド結果データ構造・状態管理・型定義

## エンティティ設計

### 1. ResultData（結果データ）

**目的**: セッション完了後の診断結果を包含する最上位エンティティ

```typescript
interface ResultData {
  sessionId: string;           // セッション識別子（UUID v4）
  keyword: string;             // 初期選択キーワード
  axes: AxisScore[];           // 評価軸スコア配列（2-6軸）
  type: TypeResult;            // タイプ分類結果
  completedAt: string;         // 完了時刻（ISO 8601）
  themeId?: string;            // UIテーマID（将来拡張）
}
```

**バリデーション規則**:
- `sessionId`: UUID v4形式必須
- `keyword`: 1-20文字、非空文字
- `axes`: 2-6要素の配列
- `completedAt`: ISO 8601形式の日時文字列

**関係性**:
- `1:N` → AxisScore（評価軸）
- `1:1` → TypeResult（タイプ分類）

### 2. AxisScore（評価軸スコア）

**目的**: 個別評価軸のスコア情報とメタデータ

```typescript
interface AxisScore {
  id: string;                  // 軸識別子（axis_1, axis_2, ...）
  name: string;                // 軸名称（日本語）
  description: string;         // 軸の詳細説明
  direction: string;           // 方向性表示（例：「論理的 ⟷ 感情的」）
  score: number;               // 正規化後スコア（0-100）
  rawScore: number;            // 正規化前スコア（-5.0 - 5.0）
  variance?: number;           // 分散値（主軸選定用）
}
```

**バリデーション規則**:
- `id`: 'axis_' prefix + 数値
- `name`: 1-20文字
- `description`: 1-100文字
- `direction`: '⟷'区切り形式
- `score`: 0-100の数値（小数第1位）
- `rawScore`: -5.0 - 5.0の数値

**状態遷移**:
- `初期`: rawScore のみ設定
- `正規化`: score が計算・設定
- `表示`: UI描画で score を使用

### 3. TypeResult（タイプ分類結果）

**目的**: 動的生成されたユーザータイプ分類情報

```typescript
interface TypeResult {
  name: string;                // タイプ名（英語1-2語、最大14文字）
  description: string;         // タイプ説明（50文字以内）
  dominantAxes: string[];      // 主軸ID配列（2要素固定）
  polarity: string;            // 極性パターン（Hi-Lo, Hi-Hi等）
  keywords?: string[];         // 関連キーワード（将来拡張）
  confidence?: number;         // 信頼度（将来拡張）
}
```

**バリデーション規則**:
- `name`: 英語1-2語、14文字以内、重複禁止
- `description`: 50文字以内
- `dominantAxes`: 2要素の軸ID配列
- `polarity`: Hi/Lo/Mid の組み合わせ

**極性パターン**:
- `Hi-Hi`: 両軸とも高スコア（≥60）
- `Hi-Lo`: 軸A高・軸B低
- `Lo-Hi`: 軸A低・軸B高
- `Lo-Lo`: 両軸とも低スコア（≤40）
- `Hi-Mid`, `Lo-Mid`, `Mid-Hi`, `Mid-Lo`: 片軸中間値
- `Mid-Mid`: 両軸中間値

## 状態管理設計

### 1. ResultScreenState（画面状態）

```typescript
interface ResultScreenState {
  // データ状態
  result: ResultData | null;
  isLoading: boolean;
  error: string | null;
  
  // UI状態
  animationStates: {
    [axisId: string]: {
      isAnimating: boolean;
      animatedScore: number;
      animationStartTime?: number;
    };
  };
  
  // インタラクション状態
  expandedAxisId: string | null;  // 詳細表示中の軸
  retryAttempts: number;          // API再試行回数
}
```

### 2. ResultActions（アクション定義）

```typescript
type ResultAction =
  | { type: 'FETCH_RESULT_START'; payload: { sessionId: string } }
  | { type: 'FETCH_RESULT_SUCCESS'; payload: { result: ResultData } }
  | { type: 'FETCH_RESULT_ERROR'; payload: { error: string } }
  | { type: 'START_AXIS_ANIMATION'; payload: { axisId: string; targetScore: number } }
  | { type: 'UPDATE_AXIS_ANIMATION'; payload: { axisId: string; animatedScore: number } }
  | { type: 'COMPLETE_AXIS_ANIMATION'; payload: { axisId: string } }
  | { type: 'TOGGLE_AXIS_DETAILS'; payload: { axisId: string } }
  | { type: 'RESET_STATE' };
```

### 3. State Reducer

```typescript
const resultReducer = (
  state: ResultScreenState, 
  action: ResultAction
): ResultScreenState => {
  switch (action.type) {
    case 'FETCH_RESULT_START':
      return {
        ...state,
        isLoading: true,
        error: null,
        retryAttempts: state.retryAttempts + 1
      };
      
    case 'FETCH_RESULT_SUCCESS':
      const { result } = action.payload;
      return {
        ...state,
        result,
        isLoading: false,
        error: null,
        animationStates: initializeAnimationStates(result.axes)
      };
      
    case 'START_AXIS_ANIMATION':
      return {
        ...state,
        animationStates: {
          ...state.animationStates,
          [action.payload.axisId]: {
            isAnimating: true,
            animatedScore: 0,
            animationStartTime: performance.now()
          }
        }
      };
      
    default:
      return state;
  }
};
```

## API契約モデル

### 1. API Request

```typescript
// GET /api/sessions/{sessionId}/result
interface GetResultRequest {
  sessionId: string;  // Path parameter
}
```

### 2. API Response

```typescript
interface GetResultResponse extends ResultData {
  // ResultData と同一構造
  // API契約の詳細は contracts/ で定義
}
```

### 3. エラーレスポンス

```typescript
interface ErrorResponse {
  error: {
    code: string;           // エラーコード
    message: string;        // エラーメッセージ
    details?: any;          // 詳細情報
  };
  sessionId?: string;       // セッションID（参照用）
}

// エラーコード一覧
type ErrorCode = 
  | 'SESSION_NOT_FOUND'     // 404: セッション未存在
  | 'SESSION_NOT_COMPLETED' // 400: 診断未完了
  | 'TYPE_GEN_FAILED'       // 500: タイプ生成失敗
  | 'INVALID_SESSION_STATE' // 400: セッション状態不正
  | 'NETWORK_ERROR'         // クライアントサイドネットワークエラー
  | 'TIMEOUT_ERROR';        // クライアントサイドタイムアウト
```

## データ変換・正規化

### 1. スコア正規化

```typescript
interface ScoreNormalization {
  // 理論値範囲: キーワード修正(-1.0~1.0) + 4シーン重み(-4.0~4.0) = -5.0~5.0
  readonly MIN_RAW_SCORE = -5.0;
  readonly MAX_RAW_SCORE = 5.0;
  
  // 正規化式: (raw - min) / (max - min) * 100
  normalizeScore(rawScore: number): number {
    return Math.max(0, Math.min(100, 
      (rawScore - this.MIN_RAW_SCORE) / 
      (this.MAX_RAW_SCORE - this.MIN_RAW_SCORE) * 100
    ));
  }
}
```

### 2. アニメーション用データ変換

```typescript
interface AnimationData {
  axisId: string;
  startScore: number;      // 常に0
  endScore: number;        // 最終スコア
  duration: number;        // 1000ms固定
  easing: string;          // 'ease-out'固定
}

const createAnimationData = (axis: AxisScore): AnimationData => ({
  axisId: axis.id,
  startScore: 0,
  endScore: axis.score,
  duration: 1000,
  easing: 'ease-out'
});
```

## パフォーマンス考慮事項

### 1. メモリ管理

```typescript
// WeakMap によるセッション単位データ管理
const sessionDataCache = new WeakMap<ResultData, ProcessedData>();

// メモリリーク防止
useEffect(() => {
  return () => {
    // コンポーネントアンマウント時のクリーンアップ
    setResult(null);
    setAnimationStates({});
  };
}, []);
```

### 2. 計算最適化

```typescript
// 重い計算のメモ化
const processedAxes = useMemo(() => {
  if (!result) return [];
  
  return result.axes.map(axis => ({
    ...axis,
    // 事前計算した値をキャッシュ
    animationDelay: calculateAnimationDelay(axis.id),
    displayPosition: calculatePosition(axis.score)
  }));
}, [result]);
```

## バリデーション規則

### 1. 実行時バリデーション

```typescript
const validateResultData = ( unknown): data is ResultData => {
  if (!data || typeof data !== 'object') return false;
  
  const result = data as ResultData;
  
  // sessionId validation
  if (!result.sessionId || !/^[0-9a-f-]{36}$/i.test(result.sessionId)) {
    return false;
  }
  
  // axes validation
  if (!Array.isArray(result.axes) || 
      result.axes.length < 2 || 
      result.axes.length > 6) {
    return false;
  }
  
  // 各軸のスコア範囲チェック
  return result.axes.every(axis => 
    axis.score >= 0 && axis.score <= 100
  );
};
```

### 2. 型ガード

```typescript
const isAxisScore = (obj: unknown): obj is AxisScore => {
  if (!obj || typeof obj !== 'object') return false;
  const axis = obj as AxisScore;
  
  return typeof axis.id === 'string' &&
         typeof axis.name === 'string' &&
         typeof axis.score === 'number' &&
         axis.score >= 0 && axis.score <= 100;
};
```

## テスト用モックデータ

### 1. 標準ケース（2軸）

```typescript
const mockResult2Axes: ResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  keyword: 'アート',
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考と感情的判断のバランス',
      direction: '論理的 ⟷ 感情的',
      score: 75.5,
      rawScore: 2.1
    },
    {
      id: 'axis_2',
      name: '社交性',
      description: '集団行動と個人行動の指向性',
      direction: '社交的 ⟷ 内省的',
      score: 42.3,
      rawScore: -0.8
    }
  ],
  type: {
    name: 'Logical Thinker',
    description: '論理的思考を重視し、個人での内省を好む傾向があります。',
    dominantAxes: ['axis_1', 'axis_2'],
    polarity: 'Hi-Lo'
  },
  completedAt: '2025-10-14T13:15:00Z'
};
```

### 2. 境界ケース（6軸）

```typescript
const mockResult6Axes: ResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440001',
  keyword: '冒険',
  axes: [
    // 6軸のフルセット...
  ],
  type: {
    name: 'Explorer',
    description: '新しい経験を求め、積極的に行動する傾向があります。',
    dominantAxes: ['axis_1', 'axis_3'],
    polarity: 'Hi-Mid'
  },
  completedAt: '2025-10-14T13:16:00Z'
};
```

## 設計原則

1. **不変性**: 状態更新は常に新しいオブジェクトを生成
2. **型安全性**: 全てのデータにTypeScript型を適用
3. **バリデーション**: API応答の実行時検証必須
4. **パフォーマンス**: メモ化と適切なクリーンアップ
5. **拡張性**: 将来のテーマ機能・軸数変更に対応

この設計により、型安全で保守可能な結果画面機能を実現する。

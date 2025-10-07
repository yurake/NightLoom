# フロントエンド: 結果画面表示・タイプ説明 UI 設計

## 概要
診断結果の軸スコア・タイプ名・説明を表示する画面の詳細設計。

関連 Issue: #7

## 画面構成

### ResultScreen コンポーネント

```tsx
interface ResultScreenProps {
  sessionId: string;
}

const ResultScreen: React.FC<ResultScreenProps> = ({ sessionId }) => {
  const [result, setResult] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const apiClient = new SessionApiClient(process.env.REACT_APP_API_URL);
        const data = await apiClient.getResult(sessionId);
        setResult(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [sessionId]);

  if (isLoading) {
    return <LoadingIndicator />;
  }

  if (error) {
    return <ErrorMessage error={error} />;
  }

  return (
    <div className="result-screen">
      <TypeCard type={result.type} keyword={result.keyword} />
      <AxesScores axes={result.axes} />
      <ActionButtons />
    </div>
  );
};
```

## サブコンポーネント

### 1. TypeCard

タイプ名と説明を表示するカード。

```tsx
interface TypeCardProps {
  type: TypeResult;
  keyword: string;
}

const TypeCard: React.FC<TypeCardProps> = ({ type, keyword }) => {
  return (
    <div className="type-card">
      <div className="type-header">
        <h2 className="type-name">{type.name}</h2>
        <span className="keyword-tag">キーワード: {keyword}</span>
      </div>
      <p className="type-description">{type.description}</p>
      <div className="type-metadata">
        <span className="polarity-badge">{type.polarity}</span>
      </div>
    </div>
  );
};
```

### 2. AxesScores

評価軸スコア一覧を表示。

```tsx
interface AxesScoresProps {
  axes: AxisScore[];
}

const AxesScores: React.FC<AxesScoresProps> = ({ axes }) => {
  return (
    <div className="axes-scores">
      <h3>評価軸スコア</h3>
      {axes.map(axis => (
        <AxisScoreItem key={axis.id} axis={axis} />
      ))}
    </div>
  );
};
```

### 3. AxisScoreItem

個別の評価軸スコアを表示。

```tsx
interface AxisScoreItemProps {
  axis: AxisScore;
}

const AxisScoreItem: React.FC<AxisScoreItemProps> = ({ axis }) => {
  return (
    <div className="axis-score-item">
      <div className="axis-header">
        <span className="axis-name">{axis.name}</span>
        <span className="axis-score">{axis.score.toFixed(1)}</span>
      </div>
      <div className="axis-bar">
        <div
          className="axis-bar-fill"
          style={{ width: `${axis.score}%` }}
        />
      </div>
      <div className="axis-direction">
        {axis.direction}
      </div>
      <p className="axis-description">{axis.description}</p>
    </div>
  );
};
```

### 4. ActionButtons

結果画面のアクション（再診断など）。

```tsx
const ActionButtons: React.FC = () => {
  const navigate = useNavigate();

  const handleRetry = () => {
    navigate('/');
  };

  return (
    <div className="action-buttons">
      <button onClick={handleRetry} className="retry-button">
        もう一度診断する
      </button>
    </div>
  );
};
```

## データ構造

### ResultData

```tsx
interface ResultData {
  sessionId: string;
  keyword: string;
  axes: AxisScore[];
  type: TypeResult;
  completedAt: string;
}

interface AxisScore {
  id: string;
  name: string;
  description: string;
  direction: string;
  score: number;  // 0〜100
  rawScore: number;
}

interface TypeResult {
  name: string;
  description: string;
  dominantAxes: string[];
  polarity: string;
}
```

## API 呼び出し

### getResult メソッド追加

```tsx
class SessionApiClient {
  // ... 既存メソッド

  async getResult(sessionId: string): Promise<ResultData> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/result`
    );

    if (!response.ok) {
      throw new Error('Failed to get result');
    }

    return response.json();
  }
}
```

## スタイリング

### レスポンシブ CSS

```css
.result-screen {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

/* タイプカード */
.type-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.type-name {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.keyword-tag {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
}

.type-description {
  font-size: 1.125rem;
  line-height: 1.6;
  margin-top: 1rem;
}

/* 評価軸スコア */
.axes-scores {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.axis-score-item {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.axis-score-item:last-child {
  border-bottom: none;
}

.axis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.axis-name {
  font-weight: 600;
  font-size: 1.125rem;
}

.axis-score {
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
}

.axis-bar {
  width: 100%;
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.axis-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 1s ease-out;
}

.axis-direction {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.axis-description {
  font-size: 0.875rem;
  color: #4b5563;
}

/* アクションボタン */
.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.retry-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-button:hover {
  background: #5568d3;
}

/* モバイル対応 */
@media (max-width: 767px) {
  .result-screen {
    padding: 1rem;
  }

  .type-card {
    padding: 1.5rem;
  }

  .type-name {
    font-size: 1.5rem;
  }

  .axes-scores {
    padding: 1.5rem;
  }

  .axis-score-item {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
  }
}
```

## アニメーション

### スコアバーのアニメーション

```tsx
const AxisScoreItem: React.FC<AxisScoreItemProps> = ({ axis }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(axis.score);
    }, 100);

    return () => clearTimeout(timer);
  }, [axis.score]);

  return (
    <div className="axis-score-item">
      {/* ... */}
      <div className="axis-bar">
        <div
          className="axis-bar-fill"
          style={{ width: `${animatedScore}%` }}
        />
      </div>
      {/* ... */}
    </div>
  );
};
```

## 将来拡張: テーマ切替

### FR-026 対応 (次回開発)

```tsx
interface ThemeConfig {
  gradient: string;
  textColor: string;
  accentColor: string;
}

const THEME_MAP: Record<string, ThemeConfig> = {
  default: {
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    textColor: '#ffffff',
    accentColor: '#667eea'
  },
  warm: {
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    textColor: '#ffffff',
    accentColor: '#f5576c'
  },
  cool: {
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    textColor: '#ffffff',
    accentColor: '#4facfe'
  }
};

const TypeCard: React.FC<TypeCardProps> = ({ type, keyword, theme = 'default' }) => {
  const themeConfig = THEME_MAP[theme];

  return (
    <div
      className="type-card"
      style={{
        background: themeConfig.gradient,
        color: themeConfig.textColor
      }}
    >
      {/* ... */}
    </div>
  );
};
```

## 非機能要件

### UX
- モバイル表示幅: 360px min
- スコアバーアニメーション: 1秒

### パフォーマンス
- 結果画面レンダリング: < 500ms

## テストケース

### ユニットテスト (Jest)
- [x] ResultData が正しく表示される
- [x] 軸スコアが 0〜100 の範囲内
- [x] タイプ名と説明が表示される

### E2E テスト (Playwright)
- [x] 結果画面が正しく表示される
- [x] スコアバーがアニメーションする
- [x] 「もう一度診断する」で初期画面に戻る

## 実装優先度
1. ResultScreen 基本実装
2. TypeCard コンポーネント
3. AxesScores コンポーネント
4. AxisScoreItem コンポーネント
5. スタイリング
6. スコアバーアニメーション
7. ActionButtons
8. (次回) テーマ切替機能

## 参考
- [要件定義](../requirements/overview.md) §7, §11, §15.3
- 関連 FR: FR-018, FR-026 (次回), NFR-UX-002

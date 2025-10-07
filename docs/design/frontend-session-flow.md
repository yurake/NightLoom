# フロントエンド: セッションフロー UI 設計

## 概要
initialPrompt → scene1-4 → result の画面遷移と状態管理の詳細設計。

関連 Issue: #6

## 画面構成

### 画面フロー
```
1. InitialPromptScreen (初期単語選択)
   ↓
2. SceneScreen (シーン1)
   ↓
3. SceneScreen (シーン2)
   ↓
4. SceneScreen (シーン3)
   ↓
5. SceneScreen (シーン4)
   ↓
6. ResultScreen (結果表示)
```

## コンポーネント設計

### 1. InitialPromptScreen

初期単語候補を表示し、ユーザーに選択を促す画面。

```tsx
interface InitialPromptScreenProps {
  sessionId: string;
  initialCharacter: string;
  keywordCandidates: string[];
  onKeywordSelected: (keyword: string) => void;
}

const InitialPromptScreen: React.FC<InitialPromptScreenProps> = ({
  sessionId,
  initialCharacter,
  keywordCandidates,
  onKeywordSelected
}) => {
  const [customInput, setCustomInput] = useState("");

  return (
    <div className="initial-prompt-screen">
      <h1>診断を始めましょう</h1>
      <p>「{initialCharacter}」で始まる単語を選んでください</p>

      <div className="keyword-candidates">
        {keywordCandidates.map(keyword => (
          <button
            key={keyword}
            onClick={() => onKeywordSelected(keyword)}
          >
            {keyword}
          </button>
        ))}
      </div>

      <div className="custom-input">
        <input
          type="text"
          placeholder="または自由に入力"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
        />
        <button onClick={() => onKeywordSelected(customInput)}>
          決定
        </button>
      </div>
    </div>
  );
};
```

### 2. SceneScreen

シナリオと選択肢を表示する画面。

```tsx
interface SceneScreenProps {
  sceneNumber: number;
  scenario: string;
  choices: Choice[];
  onChoiceSelected: (choiceId: string) => void;
  isLoading: boolean;
}

const SceneScreen: React.FC<SceneScreenProps> = ({
  sceneNumber,
  scenario,
  choices,
  onChoiceSelected,
  isLoading
}) => {
  return (
    <div className="scene-screen">
      <div className="scene-header">
        <span className="scene-number">Scene {sceneNumber} / 4</span>
      </div>

      <div className="scenario">
        <p>{scenario}</p>
      </div>

      <div className="choices">
        {choices.map(choice => (
          <button
            key={choice.id}
            className="choice-button"
            onClick={() => onChoiceSelected(choice.id)}
            disabled={isLoading}
          >
            {choice.text}
          </button>
        ))}
      </div>

      {isLoading && <LoadingIndicator />}
    </div>
  );
};
```

### 3. LoadingIndicator

API 呼び出し中のローディング表示。

```tsx
const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading-indicator">
      <div className="spinner" />
      <p>次のシーンを準備中...</p>
    </div>
  );
};
```

## 状態管理

### セッション状態

```tsx
interface SessionState {
  sessionId: string | null;
  initialCharacter: string | null;
  keywordCandidates: string[];
  selectedKeyword: string | null;
  currentScene: number;
  scenes: Record<number, SceneData>;
  isLoading: boolean;
  error: string | null;
}

interface SceneData {
  scenario: string;
  choices: Choice[];
}

interface Choice {
  id: string;
  text: string;
}
```

### Context/Store 設計 (React Context)

```tsx
import { createContext, useContext, useReducer } from 'react';

type SessionAction =
  | { type: 'SESSION_STARTED'; payload: { sessionId: string; initialCharacter: string; keywordCandidates: string[] } }
  | { type: 'KEYWORD_SELECTED'; payload: { keyword: string } }
  | { type: 'SCENE_LOADED'; payload: { sceneNumber: number; scene: SceneData } }
  | { type: 'CHOICE_SELECTED'; payload: { sceneNumber: number; choiceId: string } }
  | { type: 'LOADING'; payload: boolean }
  | { type: 'ERROR'; payload: string };

const sessionReducer = (state: SessionState, action: SessionAction): SessionState => {
  switch (action.type) {
    case 'SESSION_STARTED':
      return {
        ...state,
        sessionId: action.payload.sessionId,
        initialCharacter: action.payload.initialCharacter,
        keywordCandidates: action.payload.keywordCandidates,
        isLoading: false
      };
    case 'KEYWORD_SELECTED':
      return {
        ...state,
        selectedKeyword: action.payload.keyword,
        currentScene: 1,
        isLoading: true
      };
    case 'SCENE_LOADED':
      return {
        ...state,
        scenes: {
          ...state.scenes,
          [action.payload.sceneNumber]: action.payload.scene
        },
        isLoading: false
      };
    case 'CHOICE_SELECTED':
      return {
        ...state,
        currentScene: action.payload.sceneNumber + 1,
        isLoading: true
      };
    case 'LOADING':
      return {
        ...state,
        isLoading: action.payload
      };
    case 'ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };
    default:
      return state;
  }
};

const SessionContext = createContext<{
  state: SessionState;
  dispatch: React.Dispatch<SessionAction>;
} | null>(null);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, {
    sessionId: null,
    initialCharacter: null,
    keywordCandidates: [],
    selectedKeyword: null,
    currentScene: 0,
    scenes: {},
    isLoading: false,
    error: null
  });

  return (
    <SessionContext.Provider value={{ state, dispatch }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return context;
};
```

## API 呼び出し

### API クライアント

```tsx
class SessionApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async startSession(): Promise<SessionStartResponse> {
    const response = await fetch(`${this.baseUrl}/api/sessions/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error('Failed to start session');
    }

    return response.json();
  }

  async confirmKeyword(sessionId: string, keyword: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/keyword`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword, customInput: false })
      }
    );

    if (!response.ok) {
      throw new Error('Failed to confirm keyword');
    }
  }

  async getScene(sessionId: string, sceneNumber: number): Promise<SceneData> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/scenes/${sceneNumber}`
    );

    if (!response.ok) {
      throw new Error('Failed to get scene');
    }

    return response.json();
  }

  async selectChoice(
    sessionId: string,
    sceneNumber: number,
    choiceId: string
  ): Promise<{ nextScene: number | null }> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/scenes/${sceneNumber}/choice`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choiceId })
      }
    );

    if (!response.ok) {
      throw new Error('Failed to select choice');
    }

    return response.json();
  }
}
```

### カスタムフック

```tsx
export const useSessionFlow = () => {
  const { state, dispatch } = useSession();
  const apiClient = new SessionApiClient(process.env.REACT_APP_API_URL);

  const startSession = async () => {
    try {
      dispatch({ type: 'LOADING', payload: true });
      const response = await apiClient.startSession();
      dispatch({
        type: 'SESSION_STARTED',
        payload: {
          sessionId: response.sessionId,
          initialCharacter: response.initialCharacter,
          keywordCandidates: response.keywordCandidates
        }
      });
    } catch (error) {
      dispatch({ type: 'ERROR', payload: error.message });
    }
  };

  const selectKeyword = async (keyword: string) => {
    try {
      await apiClient.confirmKeyword(state.sessionId!, keyword);
      dispatch({ type: 'KEYWORD_SELECTED', payload: { keyword } });

      // シーン1を取得
      const scene = await apiClient.getScene(state.sessionId!, 1);
      dispatch({ type: 'SCENE_LOADED', payload: { sceneNumber: 1, scene } });
    } catch (error) {
      dispatch({ type: 'ERROR', payload: error.message });
    }
  };

  const selectChoice = async (sceneNumber: number, choiceId: string) => {
    try {
      const response = await apiClient.selectChoice(
        state.sessionId!,
        sceneNumber,
        choiceId
      );
      dispatch({ type: 'CHOICE_SELECTED', payload: { sceneNumber, choiceId } });

      if (response.nextScene !== null) {
        // 次のシーンを取得
        const scene = await apiClient.getScene(state.sessionId!, response.nextScene);
        dispatch({
          type: 'SCENE_LOADED',
          payload: { sceneNumber: response.nextScene, scene }
        });
      } else {
        // 結果画面へ遷移
        // (ResultScreen コンポーネント側で処理)
      }
    } catch (error) {
      dispatch({ type: 'ERROR', payload: error.message });
    }
  };

  return { state, startSession, selectKeyword, selectChoice };
};
```

## ルーティング

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const App: React.FC = () => {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<InitialPromptPage />} />
          <Route path="/scene/:sceneNumber" element={<ScenePage />} />
          <Route path="/result" element={<ResultPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
};
```

## エラーハンドリング

### エラー表示コンポーネント

```tsx
const ErrorMessage: React.FC<{ error: string }> = ({ error }) => {
  return (
    <div className="error-message">
      <p>{error}</p>
      <button onClick={() => window.location.reload()}>
        最初からやり直す
      </button>
    </div>
  );
};
```

## レスポンシブ対応

### ブレークポイント
```css
/* モバイル: 360px - 767px */
@media (max-width: 767px) {
  .scene-screen {
    padding: 1rem;
  }

  .choices {
    flex-direction: column;
  }

  .choice-button {
    width: 100%;
    margin-bottom: 0.5rem;
  }
}

/* タブレット: 768px - 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .scene-screen {
    padding: 2rem;
  }
}

/* デスクトップ: 1024px - */
@media (min-width: 1024px) {
  .scene-screen {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

## 非機能要件

### UX
- 初回操作→結果まで: 5クリック以下
- モバイル表示幅: 360px min

### パフォーマンス
- 初回レンダリング: < 1s
- 画面遷移: < 300ms

## テストケース

### ユニットテスト (Jest)
- [x] sessionReducer が正しく状態更新する
- [x] useSessionFlow フックが API を呼び出す
- [x] エラー時に適切なメッセージが表示される

### E2E テスト (Playwright)
- [x] 初期単語選択から結果画面まで遷移できる
- [x] 各シーンで選択肢をクリックできる
- [x] モバイル幅で表示が崩れない

## 実装優先度
1. SessionContext/Store 実装
2. InitialPromptScreen 実装
3. SceneScreen 実装
4. API クライアント実装
5. ルーティング設定
6. エラーハンドリング
7. レスポンシブ対応

## 参考
- [要件定義](../requirements/overview.md) §6, §7, §15.3
- 関連 FR: FR-014, FR-018, FR-025, NFR-UX-001, NFR-UX-002

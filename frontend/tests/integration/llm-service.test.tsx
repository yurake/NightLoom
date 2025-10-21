/**
 * LLM機能 フロントエンドサービス層統合テスト（正常系のみ）
 * SessionClientとLLM機能の統合動作を検証
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionClient, BootstrapResponse, SceneResponse, ResultResponse } from '../../app/services/sessionClient';
import React from 'react';

// テスト用コンポーネント
const TestComponent = () => {
  const [sessionClient] = React.useState(() => new SessionClient('/api'));
  const [bootstrapData, setBootstrapData] = React.useState<BootstrapResponse | null>(null);
  const [sceneData, setSceneData] = React.useState<SceneResponse | null>(null);
  const [resultData, setResultData] = React.useState<ResultResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleBootstrap = async () => {
    setLoading(true);
    try {
      const data = await sessionClient.bootstrap();
      setBootstrapData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordConfirm = async (keyword: string) => {
    if (!bootstrapData) return;
    setLoading(true);
    try {
      const data = await sessionClient.confirmKeyword(
        bootstrapData.sessionId,
        keyword,
        'suggestion'
      );
      setSceneData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGetResult = async () => {
    if (!bootstrapData) return;
    setLoading(true);
    try {
      const data = await sessionClient.getResult(bootstrapData.sessionId);
      setResultData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleBootstrap} disabled={loading}>
        Bootstrap
      </button>
      
      {bootstrapData && (
        <div data-testid="bootstrap-result">
          <p>Session: {bootstrapData.sessionId}</p>
          <p>Theme: {bootstrapData.themeId}</p>
          <p>Character: {bootstrapData.initialCharacter}</p>
          <p>Fallback: {bootstrapData.fallbackUsed ? 'Yes' : 'No'}</p>
          <div data-testid="keywords">
            {bootstrapData.keywordCandidates.map((keyword: string, index: number) => (
              <button
                key={index}
                onClick={() => handleKeywordConfirm(keyword)}
                data-testid={`keyword-${index}`}
              >
                {keyword}
              </button>
            ))}
          </div>
        </div>
      )}

      {sceneData && (
        <div data-testid="scene-result">
          <p>Scene Index: {sceneData.scene.sceneIndex}</p>
          <p>Narrative: {sceneData.scene.narrative}</p>
          <p>Choices: {sceneData.scene.choices.length}</p>
          <button onClick={handleGetResult}>Get Result</button>
        </div>
      )}

      {resultData && (
        <div data-testid="result-data">
          <p>Type: {resultData.type?.profiles?.[0]?.name || 'Unknown'}</p>
          <p>Axes: {resultData.axes.length}</p>
        </div>
      )}

      {loading && <div data-testid="loading">Loading...</div>}
      {error && <div data-testid="error">{error}</div>}
    </div>
  );
};

// モックデータ
const mockBootstrapResponse = {
  sessionId: 'test-session-llm-123',
  axes: [
    {
      id: 'focus_creativity',
      name: '集中と創造性',
      description: '集中力と創造性のバランス',
      direction: '集中 ⟷ 創造性',
    },
  ],
  keywordCandidates: ['てすと', 'てがみ', 'てんき', 'てつだい'],
  initialCharacter: 'て',
  themeId: 'focus',
  fallbackUsed: false,
};

const mockSceneResponse = {
  sessionId: 'test-session-llm-123',
  scene: {
    sceneIndex: 1,
    themeId: 'focus',
    narrative: 'LLMによって生成されたシーンです。集中力が試される状況です。',
    choices: [
      { id: 'choice_1_1', text: '集中して取り組む', weights: { focus: 0.8 } },
      { id: 'choice_1_2', text: '創造的にアプローチ', weights: { creativity: 0.7 } },
    ],
  },
  fallbackUsed: false,
};

const mockResultResponse = {
  sessionId: 'test-session-llm-123',
  keyword: 'てすと',
  axes: [
    {
      id: 'focus_creativity',
      name: '集中と創造性',
      description: '集中力と創造性のバランス',
      direction: '集中 ⟷ 創造性',
      score: 75,
      rawScore: 2.1,
    },
  ],
  type: {
    dominantAxes: ['focus_creativity'],
    profiles: [
      {
        name: '集中型クリエイター',
        description: '集中力と創造性を併せ持つ',
        dominantAxes: ['focus_creativity'],
        polarity: 'Hi-Lo',
      },
    ],
  },
  completedAt: '2024-01-01T10:00:00Z',
  fallbackFlags: [],
};

describe('LLM Service Integration Tests', () => {
  let fetchMock: jest.SpiedFunction<typeof fetch>;

  beforeAll(() => {
    fetchMock = jest.spyOn(globalThis, 'fetch');
  });

  afterEach(() => {
    fetchMock.mockReset();
    jest.clearAllMocks();
  });

  afterAll(() => {
    fetchMock.mockRestore();
  });

  const setupSuccessfulMocks = () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockBootstrapResponse),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockSceneResponse),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResultResponse),
      } as Response);
  };

  test('should complete full LLM integration flow successfully', async () => {
    setupSuccessfulMocks();

    render(<TestComponent />);

    // 1. Bootstrap実行
    const bootstrapButton = screen.getByText('Bootstrap');
    await act(async () => {
      await userEvent.click(bootstrapButton);
    });

    // Bootstrap結果の確認
    await waitFor(() => {
      expect(screen.getByTestId('bootstrap-result')).toBeInTheDocument();
    });

    expect(screen.getByText('Session: test-session-llm-123')).toBeInTheDocument();
    expect(screen.getByText('Theme: focus')).toBeInTheDocument();
    expect(screen.getByText('Character: て')).toBeInTheDocument();
    expect(screen.getByText('Fallback: No')).toBeInTheDocument();

    // LLM生成キーワードの確認
    const keywordsContainer = screen.getByTestId('keywords');
    expect(keywordsContainer).toBeInTheDocument();
    
    const keywordButtons = screen.getAllByTestId(/^keyword-/);
    expect(keywordButtons).toHaveLength(4);
    expect(screen.getByText('てすと')).toBeInTheDocument();

    // 2. キーワード選択
    const firstKeyword = screen.getByTestId('keyword-0');
    await act(async () => {
      await userEvent.click(firstKeyword);
    });

    // LLM生成シーン結果の確認
    await waitFor(() => {
      expect(screen.getByTestId('scene-result')).toBeInTheDocument();
    });

    expect(screen.getByText('Scene Index: 1')).toBeInTheDocument();
    expect(screen.getByText(/LLMによって生成されたシーン/)).toBeInTheDocument();
    expect(screen.getByText('Choices: 2')).toBeInTheDocument();

    // 3. 結果取得
    const resultButton = screen.getByText('Get Result');
    await act(async () => {
      await userEvent.click(resultButton);
    });

    // LLM生成結果の確認
    await waitFor(() => {
      expect(screen.getByTestId('result-data')).toBeInTheDocument();
    });

    expect(screen.getByText('Type: 集中型クリエイター')).toBeInTheDocument();
    expect(screen.getByText('Axes: 1')).toBeInTheDocument();

    // API呼び出し回数の確認
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  test('should handle LLM keyword generation with custom input', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockBootstrapResponse),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          ...mockSceneResponse,
          scene: {
            ...mockSceneResponse.scene,
            narrative: 'カスタムキーワード「てすと」で生成されたシーンです。',
          },
        }),
      } as Response);

    render(<TestComponent />);

    // Bootstrap実行
    await act(async () => {
      await userEvent.click(screen.getByText('Bootstrap'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('bootstrap-result')).toBeInTheDocument();
    });

    // カスタムキーワード選択
    await act(async () => {
      await userEvent.click(screen.getByText('てすと'));
    });

    // カスタムキーワードによるLLM生成結果確認
    await waitFor(() => {
      expect(screen.getByText(/カスタムキーワード「てすと」で生成/)).toBeInTheDocument();
    });
  });

  test('should handle LLM fallback scenarios', async () => {
    const fallbackBootstrapResponse = {
      ...mockBootstrapResponse,
      keywordCandidates: ['フォールバック1', 'フォールバック2', 'フォールバック3', 'フォールバック4'],
      fallbackUsed: true,
    };

    const fallbackSceneResponse = {
      ...mockSceneResponse,
      scene: {
        ...mockSceneResponse.scene,
        narrative: 'フォールバック機能によって生成されたシーンです。',
      },
      fallbackUsed: true,
    };

    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(fallbackBootstrapResponse),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(fallbackSceneResponse),
      } as Response);

    render(<TestComponent />);

    // Bootstrap実行
    await act(async () => {
      await userEvent.click(screen.getByText('Bootstrap'));
    });

    await waitFor(() => {
      expect(screen.getByText('Fallback: Yes')).toBeInTheDocument();
    });

    // フォールバックキーワードの確認
    expect(screen.getByText('フォールバック1')).toBeInTheDocument();

    // フォールバックキーワード選択
    await act(async () => {
      await userEvent.click(screen.getByText('フォールバック1'));
    });

    // フォールバックシーンの確認
    await waitFor(() => {
      expect(screen.getByText(/フォールバック機能によって生成/)).toBeInTheDocument();
    });
  });

  test('should handle SessionClient error states', async () => {
    // Bootstrap失敗をシミュレート
    fetchMock.mockRejectedValueOnce(new Error('LLM service unavailable'));

    render(<TestComponent />);

    await act(async () => {
      await userEvent.click(screen.getByText('Bootstrap'));
    });

    // エラー状態の確認
    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument();
    });

    expect(screen.getByText(/Network error during bootstrap/)).toBeInTheDocument();
  });

  test('should maintain session state across LLM operations', async () => {
    setupSuccessfulMocks();

    render(<TestComponent />);

    // Bootstrap実行
    await act(async () => {
      await userEvent.click(screen.getByText('Bootstrap'));
    });

    await waitFor(() => {
      expect(screen.getByText('Session: test-session-llm-123')).toBeInTheDocument();
    });

    // キーワード選択（同じセッションIDを使用）
    await act(async () => {
      await userEvent.click(screen.getByTestId('keyword-0'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('scene-result')).toBeInTheDocument();
    });

    // セッションIDが一貫して使用されていることを確認
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/sessions/test-session-llm-123/keyword',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  test('should handle LLM processing delays', async () => {
    // 遅延を持つレスポンスをシミュレート
    fetchMock.mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve(mockBootstrapResponse),
              } as Response),
            500
          )
        )
    );

    render(<TestComponent />);

    // Bootstrap実行
    await act(async () => {
      await userEvent.click(screen.getByText('Bootstrap'));
    });

    // ローディング状態の確認
    expect(screen.getByTestId('loading')).toBeInTheDocument();

    // 遅延後の結果確認
    await waitFor(
      () => {
        expect(screen.getByTestId('bootstrap-result')).toBeInTheDocument();
      },
      { timeout: 1000 }
    );

    // ローディングが終了していることを確認
    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
  });
});


/**
 * SessionContext テスト
 * セッション状態管理、状態遷移、エラーハンドリング、リトライロジックのテスト
 */

import React from 'react';
import { render, renderHook, act, screen } from '@testing-library/react';
import {
  SessionProvider,
  useSession,
  sessionActions,
  useSessionId,
  useCurrentScene,
  useSessionProgress,
  useSessionResult,
  useSessionTheme,
  validateSessionState,
  SessionContextState
} from '../../app/state/SessionContext';
import { Session, Scene, AxisScore, TypeProfile } from '../../app/types/session';

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <SessionProvider>{children}</SessionProvider>
);

// Mock data
const mockSession: Session = {
  id: 'test-session-123',
  state: 'INIT',
  themeId: 'adventure',
  keywordCandidates: ['冒険', '成長', '挑戦'],
  initialCharacter: 'brave_explorer',
  scenes: [],
  choices: [],
  rawScores: {},
  normalizedScores: {},
  typeProfiles: [],
  fallbackFlags: [],
  createdAt: '2024-01-01T09:00:00Z'
};

const mockScene: Scene = {
  sceneIndex: 1,
  themeId: 'adventure',
  narrative: 'テストシナリオです。',
  choices: [
    {
      id: 'choice_1_1',
      text: '選択肢1',
      weights: { axis_1: 1.0 }
    },
    {
      id: 'choice_1_2',
      text: '選択肢2',
      weights: { axis_1: -1.0 }
    }
  ]
};

const mockAxesScores: AxisScore[] = [
  {
    axisId: 'axis_1',
    score: 75.5,
    rawScore: 2.1
  }
];

const mockTypeProfiles: TypeProfile[] = [
  {
    name: 'Logic Thinker',
    description: '論理的思考を重視する',
    dominantAxes: ['axis_1', 'axis_2'],
    polarity: 'Hi-Lo'
  }
];

describe('SessionContext', () => {
  describe('SessionProvider', () => {
    it('初期状態が正しく設定される', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      expect(result.current.state).toEqual({
        session: null,
        currentScene: null,
        currentSceneIndex: 0,
        isLoading: false,
        error: null,
        completedScenes: [],
        canProceedToResult: false,
        result: null
      });
    });

    it('dispatchが提供される', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      expect(result.current.dispatch).toBeDefined();
      expect(typeof result.current.dispatch).toBe('function');
    });
  });

  describe('useSession hook', () => {
    it('Provider外で使用するとエラーを投げる', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        renderHook(() => useSession());
      }).toThrow('useSession must be used within a SessionProvider');
      
      consoleSpy.mockRestore();
    });

    it('Provider内で正常に動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      expect(result.current.state).toBeDefined();
      expect(result.current.dispatch).toBeDefined();
    });
  });

  describe('セッション状態遷移', () => {
    it('SET_LOADING アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      act(() => {
        result.current.dispatch(sessionActions.setLoading(true));
      });

      expect(result.current.state.isLoading).toBe(true);

      act(() => {
        result.current.dispatch(sessionActions.setLoading(false));
      });

      expect(result.current.state.isLoading).toBe(false);
    });

    it('SET_ERROR アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      const errorMessage = 'テストエラーメッセージ';

      act(() => {
        result.current.dispatch(sessionActions.setError(errorMessage));
      });

      expect(result.current.state.error).toBe(errorMessage);
      expect(result.current.state.isLoading).toBe(false);

      act(() => {
        result.current.dispatch(sessionActions.setError(null));
      });

      expect(result.current.state.error).toBeNull();
    });

    it('BOOTSTRAP_SUCCESS アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      expect(result.current.state.session).toEqual(mockSession);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it('KEYWORD_CONFIRMED アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // First bootstrap
      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      const keyword = 'テストキーワード';

      act(() => {
        result.current.dispatch(sessionActions.keywordConfirmed(keyword, mockScene));
      });

      expect(result.current.state.session?.selectedKeyword).toBe(keyword);
      expect(result.current.state.session?.state).toBe('PLAY');
      expect(result.current.state.currentScene).toEqual(mockScene);
      expect(result.current.state.currentSceneIndex).toBe(1);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it('KEYWORD_CONFIRMED がセッションなしでは何もしない', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      const initialState = result.current.state;

      act(() => {
        result.current.dispatch(sessionActions.keywordConfirmed('test', mockScene));
      });

      expect(result.current.state).toEqual(initialState);
    });

    it('LOAD_SCENE アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      act(() => {
        result.current.dispatch(sessionActions.loadScene(mockScene, 2));
      });

      expect(result.current.state.currentScene).toEqual(mockScene);
      expect(result.current.state.currentSceneIndex).toBe(2);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it('CHOICE_SUBMITTED アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      const nextScene: Scene = {
        ...mockScene,
        sceneIndex: 2
      };

      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_1', nextScene));
      });

      expect(result.current.state.completedScenes).toEqual([1]);
      expect(result.current.state.canProceedToResult).toBe(false);
      expect(result.current.state.currentScene).toEqual(nextScene);
      expect(result.current.state.currentSceneIndex).toBe(2);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it('CHOICE_SUBMITTED で全シーン完了時にcanProceedToResultがtrueになる', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // Complete all 4 scenes
      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_1'));
      });
      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(2, 'choice_2_1'));
      });
      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(3, 'choice_3_1'));
      });
      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(4, 'choice_4_1'));
      });

      expect(result.current.state.completedScenes).toEqual([1, 2, 3, 4]);
      expect(result.current.state.canProceedToResult).toBe(true);
    });

    it('CHOICE_SUBMITTED で重複したシーンは追加されない', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_1'));
      });
      act(() => {
        result.current.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_2'));
      });

      expect(result.current.state.completedScenes).toEqual([1]);
    });

    it('RESULT_GENERATED アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // Bootstrap first
      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      const completedAt = '2024-01-01T10:00:00Z';

      act(() => {
        result.current.dispatch(sessionActions.resultGenerated(
          mockAxesScores,
          mockTypeProfiles,
          completedAt
        ));
      });

      expect(result.current.state.result).toEqual({
        axes: mockAxesScores,
        typeProfiles: mockTypeProfiles,
        completedAt
      });
      expect(result.current.state.session?.state).toBe('RESULT');
      expect(result.current.state.session?.completedAt).toBe(completedAt);
      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it('RESET_SESSION アクションが正しく動作する', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // Set some state first
      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
        result.current.dispatch(sessionActions.setLoading(true));
        result.current.dispatch(sessionActions.setError('test error'));
      });

      act(() => {
        result.current.dispatch(sessionActions.resetSession());
      });

      expect(result.current.state).toEqual({
        session: null,
        currentScene: null,
        currentSceneIndex: 0,
        isLoading: false,
        error: null,
        completedScenes: [],
        canProceedToResult: false,
        result: null
      });
    });
  });

  describe('セレクターフック', () => {
    it('useSessionId が正しく動作する', () => {
      const { result } = renderHook(() => ({
        session: useSession(),
        sessionId: useSessionId()
      }), {
        wrapper: TestWrapper
      });

      expect(result.current.sessionId).toBeNull();

      act(() => {
        result.current.session.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      expect(result.current.sessionId).toBe(mockSession.id);
    });

    it('useCurrentScene が正しく動作する', () => {
      const { result } = renderHook(() => ({
        session: useSession(),
        currentScene: useCurrentScene()
      }), {
        wrapper: TestWrapper
      });

      expect(result.current.currentScene).toBeNull();

      act(() => {
        result.current.session.dispatch(sessionActions.loadScene(mockScene, 1));
      });

      expect(result.current.currentScene).toEqual(mockScene);
    });

    it('useSessionProgress が正しく動作する', () => {
      const { result } = renderHook(() => ({
        session: useSession(),
        progress: useSessionProgress()
      }), {
        wrapper: TestWrapper
      });

      expect(result.current.progress).toEqual({
        completedScenes: 0,
        totalScenes: 4,
        progressPercentage: 0,
        canProceedToResult: false
      });

      act(() => {
        result.current.session.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_1'));
        result.current.session.dispatch(sessionActions.choiceSubmitted(2, 'choice_2_1'));
      });

      expect(result.current.progress).toEqual({
        completedScenes: 2,
        totalScenes: 4,
        progressPercentage: 50,
        canProceedToResult: false
      });
    });

    it('useSessionResult が正しく動作する', () => {
      const { result } = renderHook(() => ({
        session: useSession(),
        sessionResult: useSessionResult()
      }), {
        wrapper: TestWrapper
      });

      expect(result.current.sessionResult).toBeNull();

      act(() => {
        result.current.session.dispatch(sessionActions.resultGenerated(
          mockAxesScores,
          mockTypeProfiles,
          '2024-01-01T10:00:00Z'
        ));
      });

      expect(result.current.sessionResult).toEqual({
        axes: mockAxesScores,
        typeProfiles: mockTypeProfiles,
        completedAt: '2024-01-01T10:00:00Z'
      });
    });

    it('useSessionTheme が正しく動作する', () => {
      const { result } = renderHook(() => ({
        session: useSession(),
        theme: useSessionTheme()
      }), {
        wrapper: TestWrapper
      });

      expect(result.current.theme).toBe('fallback');

      act(() => {
        result.current.session.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      expect(result.current.theme).toBe('adventure');
    });
  });

  describe('バリデーション', () => {
    it('validateSessionState が正しく動作する', () => {
      const validState: SessionContextState = {
        session: {
          ...mockSession,
          state: 'PLAY',
          selectedKeyword: 'テストキーワード'
        },
        currentScene: mockScene,
        currentSceneIndex: 1,
        isLoading: false,
        error: null,
        completedScenes: [1],
        canProceedToResult: false,
        result: null
      };

      const errors = validateSessionState(validState);
      expect(errors).toEqual([]);
    });

    it('validateSessionState がPLAY状態でselectedKeywordがない場合エラーを返す', () => {
      const invalidState: SessionContextState = {
        session: {
          ...mockSession,
          state: 'PLAY'
        },
        currentScene: mockScene,
        currentSceneIndex: 1,
        isLoading: false,
        error: null,
        completedScenes: [],
        canProceedToResult: false,
        result: null
      };

      const errors = validateSessionState(invalidState);
      expect(errors).toContain('Selected keyword is required in PLAY state');
    });

    it('validateSessionState が完了シーン数が4を超える場合エラーを返す', () => {
      const invalidState: SessionContextState = {
        session: {
          ...mockSession,
          state: 'PLAY',
          selectedKeyword: 'test'
        },
        currentScene: mockScene,
        currentSceneIndex: 5,
        isLoading: false,
        error: null,
        completedScenes: [1, 2, 3, 4, 5],
        canProceedToResult: true,
        result: null
      };

      const errors = validateSessionState(invalidState);
      expect(errors).toContain('Cannot have more than 4 completed scenes');
    });

    it('validateSessionState がRESULT状態でresultがない場合エラーを返す', () => {
      const invalidState: SessionContextState = {
        session: {
          ...mockSession,
          state: 'RESULT'
        },
        currentScene: null,
        currentSceneIndex: 4,
        isLoading: false,
        error: null,
        completedScenes: [1, 2, 3, 4],
        canProceedToResult: true,
        result: null
      };

      const errors = validateSessionState(invalidState);
      expect(errors).toContain('Result data is required in RESULT state');
    });
  });

  describe('エラーハンドリング', () => {
    it('エラー状態が正しく管理される', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      const errorMessage = 'ネットワークエラー';

      act(() => {
        result.current.dispatch(sessionActions.setError(errorMessage));
      });

      expect(result.current.state.error).toBe(errorMessage);
      expect(result.current.state.isLoading).toBe(false);

      // Clear error
      act(() => {
        result.current.dispatch(sessionActions.setError(null));
      });

      expect(result.current.state.error).toBeNull();
    });

    it('ローディング状態とエラー状態の相互作用', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // Start loading
      act(() => {
        result.current.dispatch(sessionActions.setLoading(true));
      });

      expect(result.current.state.isLoading).toBe(true);
      expect(result.current.state.error).toBeNull();

      // Set error (should clear loading)
      act(() => {
        result.current.dispatch(sessionActions.setError('エラー'));
      });

      expect(result.current.state.isLoading).toBe(false);
      expect(result.current.state.error).toBe('エラー');
    });
  });

  describe('複合的な状態遷移', () => {
    it('完全な診断フローの状態遷移', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // 1. Bootstrap
      act(() => {
        result.current.dispatch(sessionActions.setLoading(true));
      });
      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
      });

      expect(result.current.state.session).toEqual(mockSession);
      expect(result.current.state.isLoading).toBe(false);

      // 2. Keyword confirmation
      act(() => {
        result.current.dispatch(sessionActions.keywordConfirmed('冒険', mockScene));
      });

      expect(result.current.state.session?.selectedKeyword).toBe('冒険');
      expect(result.current.state.session?.state).toBe('PLAY');
      expect(result.current.state.currentScene).toEqual(mockScene);

      // 3. Progress through scenes
      for (let i = 1; i <= 4; i++) {
        act(() => {
          result.current.dispatch(sessionActions.choiceSubmitted(i, `choice_${i}_1`));
        });
      }

      expect(result.current.state.completedScenes).toEqual([1, 2, 3, 4]);
      expect(result.current.state.canProceedToResult).toBe(true);

      // 4. Generate result
      act(() => {
        result.current.dispatch(sessionActions.resultGenerated(
          mockAxesScores,
          mockTypeProfiles,
          '2024-01-01T10:00:00Z'
        ));
      });

      expect(result.current.state.session?.state).toBe('RESULT');
      expect(result.current.state.result).toBeDefined();
    });

    it('セッションリセット後の初期状態復帰', () => {
      const { result } = renderHook(() => useSession(), {
        wrapper: TestWrapper
      });

      // Set up complex state
      act(() => {
        result.current.dispatch(sessionActions.bootstrapSuccess(mockSession));
        result.current.dispatch(sessionActions.keywordConfirmed('test', mockScene));
        result.current.dispatch(sessionActions.choiceSubmitted(1, 'choice_1_1'));
        result.current.dispatch(sessionActions.setError('test error'));
      });

      // Reset
      act(() => {
        result.current.dispatch(sessionActions.resetSession());
      });

      // Verify initial state
      expect(result.current.state).toEqual({
        session: null,
        currentScene: null,
        currentSceneIndex: 0,
        isLoading: false,
        error: null,
        completedScenes: [],
        canProceedToResult: false,
        result: null
      });
    });
  });
});

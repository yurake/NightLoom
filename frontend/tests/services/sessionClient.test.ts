/**
 * SessionClient サービスのユニットテスト
 * API クライアントのメソッド、エラーハンドリング、パフォーマンス追跡をテスト
 */

import { SessionClient, SessionAPIError, BootstrapResponse, SceneResponse, ChoiceResponse, ResultResponse } from '../../app/services/sessionClient';
import { performanceService } from '../../app/services/performance';

// MSW setup
// Mock performance service
jest.mock('../../app/services/performance', () => ({
  performanceService: {
    trackApiCall: jest.fn(),
    recordMetric: jest.fn(),
  }
}));

const mockPerformanceService = performanceService as jest.Mocked<typeof performanceService>;

// Mock data
const mockBootstrapResponse: BootstrapResponse = {
  sessionId: 'test-session-123',
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考と感情的判断のバランス',
      direction: '論理的 ⟷ 感情的'
    }
  ],
  keywordCandidates: ['冒険', '成長', '挑戦'],
  initialCharacter: 'brave_explorer',
  themeId: 'adventure'
};

const mockSceneResponse: SceneResponse = {
  sessionId: 'test-session-123',
  scene: {
    sceneIndex: 1,
    themeId: 'adventure',
    narrative: 'テストシナリオです。',
    choices: [
      {
        id: 'choice_1_1',
        text: '選択肢1',
        weights: { axis_1: 1.0 }
      }
    ]
  }
};

const mockChoiceResponse: ChoiceResponse = {
  sessionId: 'test-session-123',
  nextScene: {
    sceneIndex: 2,
    themeId: 'adventure',
    narrative: '次のシナリオです。',
    choices: []
  },
  sceneCompleted: true
};

const mockResultResponse: ResultResponse = {
  sessionId: 'test-session-123',
  keyword: '冒険',
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考と感情的判断のバランス',
      direction: '論理的 ⟷ 感情的',
      score: 75.5,
      rawScore: 2.1
    }
  ],
  type: {
    dominantAxes: ['axis_1'],
    profiles: [
      {
        name: 'Logic Thinker',
        description: '論理的思考を重視する',
        dominantAxes: ['axis_1', 'axis_2'],
        polarity: 'Hi-Lo'
      }
    ]
  },
  completedAt: '2024-01-01T10:00:00Z',
  fallbackFlags: []
};

const createJsonResponse = <T>(
  data: T,
  init: { status?: number; statusText?: string } = {}
): Response => {
  const status = init.status ?? 200;
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: init.statusText ?? 'OK',
    json: jest.fn().mockResolvedValue(data),
  } as unknown as Response;
};

describe('SessionClient', () => {
  let sessionClient: SessionClient;
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

  beforeEach(() => {
    sessionClient = new SessionClient('/api');
    mockPerformanceService.trackApiCall.mockReturnValue({
      endpoint: '/test',
      method: 'POST',
      duration: 100,
      status: 200,
      success: true,
      timestamp: Date.now()
    });
  });

  describe('constructor', () => {
    it('デフォルトのbaseURLが設定される', () => {
      const client = new SessionClient();
      expect(client['baseUrl']).toBe('/api');
    });

    it('カスタムbaseURLが設定される', () => {
      const client = new SessionClient('/custom-api');
      expect(client['baseUrl']).toBe('/custom-api');
    });

    it('末尾のスラッシュが除去される', () => {
      const client = new SessionClient('/api/');
      expect(client['baseUrl']).toBe('/api');
    });
  });

  describe('bootstrap()', () => {
    it('成功時に正しいレスポンスを返す', async () => {
      fetchMock.mockResolvedValue(createJsonResponse(mockBootstrapResponse));

      const result = await sessionClient.bootstrap();

      expect(result).toEqual(mockBootstrapResponse);
      expect(mockPerformanceService.trackApiCall).toHaveBeenCalledWith(
        '/sessions/start',
        'POST',
        expect.any(Number),
        200
      );
      expect(mockPerformanceService.recordMetric).toHaveBeenCalledWith(
        'bootstrap',
        100,
        true,
        {
          sessionId: 'test-session-123',
          fallbackUsed: undefined
        }
      );
    });

    it('HTTPエラー時にSessionAPIErrorを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 500, statusText: 'Internal Server Error' })
      );

      await expect(sessionClient.bootstrap()).rejects.toThrow(SessionAPIError);
      await expect(sessionClient.bootstrap()).rejects.toThrow('Bootstrap failed: Internal Server Error');
    });

    it('ネットワークエラー時にSessionAPIErrorを投げる', async () => {
      fetchMock.mockRejectedValue(new Error('Network error during bootstrap'));

      await expect(sessionClient.bootstrap()).rejects.toThrow(SessionAPIError);
      await expect(sessionClient.bootstrap()).rejects.toThrow(/Network error during bootstrap/);
    });
  });

  describe('confirmKeyword()', () => {
    const sessionId = 'test-session-123';
    const keyword = 'テストキーワード';

    it('成功時に正しいレスポンスを返す', async () => {
      fetchMock.mockResolvedValue(createJsonResponse(mockSceneResponse));

      const result = await sessionClient.confirmKeyword(sessionId, keyword, 'suggestion');

      expect(result).toEqual(mockSceneResponse);
      expect(mockPerformanceService.trackApiCall).toHaveBeenCalledWith(
        `/sessions/${sessionId}/keyword`,
        'POST',
        expect.any(Number),
        200
      );
    });

    it('404エラー時に適切なエラーコードを設定', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 404, statusText: 'Not Found' })
      );

      await expect(sessionClient.confirmKeyword(sessionId, keyword, 'suggestion'))
        .rejects.toThrow(SessionAPIError);
      
      try {
        await sessionClient.confirmKeyword(sessionId, keyword, 'suggestion');
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('SESSION_NOT_FOUND');
      }
    });

    it('400エラー時に適切なエラーコードを設定', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 400, statusText: 'Bad Request' })
      );

      try {
        await sessionClient.confirmKeyword(sessionId, keyword, 'suggestion');
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('INVALID_KEYWORD');
      }
    });
  });

  describe('getScene()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;

    it('成功時に正しいレスポンスを返す', async () => {
      fetchMock.mockResolvedValue(createJsonResponse(mockSceneResponse));

      const result = await sessionClient.getScene(sessionId, sceneIndex);

      expect(result).toEqual(mockSceneResponse);
    });

    it('404エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 404, statusText: 'Not Found' })
      );

      try {
        await sessionClient.getScene(sessionId, sceneIndex);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('SESSION_NOT_FOUND');
      }
    });

    it('400エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 400, statusText: 'Bad Request' })
      );

      try {
        await sessionClient.getScene(sessionId, sceneIndex);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('INVALID_SCENE_ACCESS');
      }
    });
  });

  describe('submitChoice()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;
    const choiceId = 'choice_1_1';

    it('成功時に正しいレスポンスを返す', async () => {
      fetchMock.mockResolvedValue(createJsonResponse(mockChoiceResponse));

      const result = await sessionClient.submitChoice(sessionId, sceneIndex, choiceId);

      expect(result).toEqual(mockChoiceResponse);
    });

    it('404エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 404, statusText: 'Not Found' })
      );

      try {
        await sessionClient.submitChoice(sessionId, sceneIndex, choiceId);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('SESSION_NOT_FOUND');
      }
    });

    it('400エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 400, statusText: 'Bad Request' })
      );

      try {
        await sessionClient.submitChoice(sessionId, sceneIndex, choiceId);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('INVALID_CHOICE');
      }
    });
  });

  describe('getResult()', () => {
    const sessionId = 'test-session-123';

    it('成功時に正しいレスポンスを返す', async () => {
      fetchMock.mockResolvedValue(createJsonResponse(mockResultResponse));

      const result = await sessionClient.getResult(sessionId);

      expect(result).toEqual(mockResultResponse);
      expect(mockPerformanceService.trackApiCall).toHaveBeenCalledWith(
        `/sessions/${sessionId}/result`,
        'POST',
        expect.any(Number),
        200
      );
      expect(mockPerformanceService.recordMetric).toHaveBeenCalledWith(
        'result_calculation',
        100,
        true,
        {
          sessionId,
          axisCount: 1,
          profileCount: 1,
          fallbackUsed: false
        }
      );
    });

    it('404エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 404, statusText: 'Not Found' })
      );

      try {
        await sessionClient.getResult(sessionId);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('SESSION_NOT_FOUND');
      }
    });

    it('400エラー時に適切なエラーを投げる', async () => {
      fetchMock.mockResolvedValue(
        createJsonResponse(null, { status: 400, statusText: 'Bad Request' })
      );

      try {
        await sessionClient.getResult(sessionId);
      } catch (error) {
        expect(error).toBeInstanceOf(SessionAPIError);
        expect((error as SessionAPIError).code).toBe('SESSION_NOT_COMPLETED');
      }
    });
  });
});

describe('SessionAPIError', () => {
  it('メッセージのみで作成できる', () => {
    const error = new SessionAPIError('Test error');
    expect(error.message).toBe('Test error');
    expect(error.name).toBe('SessionAPIError');
    expect(error.status).toBeUndefined();
    expect(error.code).toBeUndefined();
  });

  it('ステータスコード付きで作成できる', () => {
    const error = new SessionAPIError('Test error', 404);
    expect(error.message).toBe('Test error');
    expect(error.status).toBe(404);
    expect(error.code).toBeUndefined();
  });

  it('エラーコード付きで作成できる', () => {
    const error = new SessionAPIError('Test error', 404, 'NOT_FOUND');
    expect(error.message).toBe('Test error');
    expect(error.status).toBe(404);
    expect(error.code).toBe('NOT_FOUND');
  });
});

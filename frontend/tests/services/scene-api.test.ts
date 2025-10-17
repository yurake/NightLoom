
/**
 * Scene API サービスのユニットテスト
 * エラーハンドリング、バリデーション、ユーティリティ関数をテスト
 */

import {
  SceneApiService,
  getSceneFromChoiceId,
  getChoiceFromChoiceId,
  isValidChoiceId,
  generateChoiceId,
  calculateProgressPercentage,
  canProceedToResult,
  getNextSceneIndex,
  formatSceneText,
  formatProgressText,
  isSceneNotFoundError,
  isInvalidSceneError,
  isChoiceValidationError,
  isServiceUnavailableError,
  getSceneErrorMessage
} from '../../app/services/scene-api';
import { SessionAPIError } from '../../app/services/sessionClient';

// MSW setup
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Mock data
const mockSceneResponse = {
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
      },
      {
        id: 'choice_1_2',
        text: '選択肢2',
        weights: { axis_1: -1.0 }
      }
    ]
  }
};

const mockChoiceResponse = {
  sessionId: 'test-session-123',
  nextScene: {
    sceneIndex: 2,
    themeId: 'adventure',
    narrative: '次のシナリオです。',
    choices: []
  },
  sceneCompleted: true
};

const mockProgressResponse = {
  sessionId: 'test-session-123',
  state: 'PLAY',
  completedScenes: 2,
  totalScenes: 4,
  currentScene: 3,
  progressPercentage: 50,
  canProceedToResult: false,
  selectedKeyword: 'テストキーワード',
  themeId: 'adventure'
};

const mockValidationResponse = {
  sessionId: 'test-session-123',
  sceneIndex: 1,
  accessible: true,
  currentState: 'PLAY',
  completedScenes: 0
};

// MSW server setup
const server = setupServer();

describe('SceneApiService', () => {
  let sceneApiService: SceneApiService;

  beforeAll(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
    jest.clearAllMocks();
  });

  afterAll(() => {
    server.close();
  });

  beforeEach(() => {
    sceneApiService = new SceneApiService('/api');
  });

  describe('constructor', () => {
    it('デフォルトのbaseURLが設定される', () => {
      const service = new SceneApiService();
      expect(service['baseUrl']).toBe('/api');
    });

    it('カスタムbaseURLが設定される', () => {
      const service = new SceneApiService('/custom-api');
      expect(service['baseUrl']).toBe('/custom-api');
    });
  });

  describe('getScene()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;

    it('成功時に正しいレスポンスを返す', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/scenes/${sceneIndex}`, (req, res, ctx) => {
          return res(ctx.json(mockSceneResponse));
        })
      );

      const result = await sceneApiService.getScene(sessionId, sceneIndex);

      expect(result).toEqual(mockSceneResponse);
    });

    it('APIエラー時に適切なエラーを投げる', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/scenes/${sceneIndex}`, (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ error: { code: 'SESSION_NOT_FOUND', message: 'Session not found' } })
          );
        })
      );

      await expect(sceneApiService.getScene(sessionId, sceneIndex))
        .rejects.toThrow(SessionAPIError);
    });

    it('ネットワークエラー時にSessionAPIErrorを投げる', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/scenes/${sceneIndex}`, (req, res, ctx) => {
          return res.networkError('Network error');
        })
      );

      await expect(sceneApiService.getScene(sessionId, sceneIndex))
        .rejects.toThrow(SessionAPIError);
    });

    it('JSON解析エラー時にSessionAPIErrorを投げる', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/scenes/${sceneIndex}`, (req, res, ctx) => {
          return res(ctx.status(500), ctx.text('invalid json'));
        })
      );

      await expect(sceneApiService.getScene(sessionId, sceneIndex))
        .rejects.toThrow(SessionAPIError);
    });
  });

  describe('submitChoice()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;
    const choiceId = 'choice_1_1';

    it('成功時に正しいレスポンスを返す', async () => {
      server.use(
        rest.post(`/api/sessions/${sessionId}/scenes/${sceneIndex}/choice`, (req, res, ctx) => {
          return res(ctx.json(mockChoiceResponse));
        })
      );

      const result = await sceneApiService.submitChoice(sessionId, sceneIndex, choiceId);

      expect(result).toEqual(mockChoiceResponse);
    });

    it('バリデーションエラー時に適切なエラーを投げる', async () => {
      server.use(
        rest.post(`/api/sessions/${sessionId}/scenes/${sceneIndex}/choice`, (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ error: { code: 'VALIDATION_ERROR', message: 'Invalid choice' } })
          );
        })
      );

      await expect(sceneApiService.submitChoice(sessionId, sceneIndex, choiceId))
        .rejects.toThrow(SessionAPIError);
    });
  });

  describe('getProgress()', () => {
    const sessionId = 'test-session-123';

    it('成功時に正しいレスポンスを返す', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/progress`, (req, res, ctx) => {
          return res(ctx.json(mockProgressResponse));
        })
      );

      const result = await sceneApiService.getProgress(sessionId);

      expect(result).toEqual(mockProgressResponse);
    });

    it('セッションが見つからない場合のエラーハンドリング', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/progress`, (req, res, ctx) => {
          return res(ctx.status(404));
        })
      );

      await expect(sceneApiService.getProgress(sessionId))
        .rejects.toThrow(SessionAPIError);
    });
  });

  describe('validateSceneAccess()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;

    it('成功時に正しいレスポンスを返す', async () => {
      server.use(
        rest.get(`/api/sessions/${sessionId}/scenes/${sceneIndex}/validate`, (req, res, ctx) => {
          return res(ctx.json(mockValidationResponse));
        })
      );

      const result = await sceneApiService.validateSceneAccess(sessionId, sceneIndex);

      expect(result).toEqual(mockValidationResponse);
    });
  });

  describe('validateChoice()', () => {
    const sessionId = 'test-session-123';
    const sceneIndex = 1;
    const choiceId = 'choice_1_1';

    it('成功時に正しいレスポンスを返す', async () => {
      const mockValidationResult = {
        valid: true,
        formatValid: true,
        choiceExists: true
      };

      server.use(
        rest.post(`/api/sessions/${sessionId}/scenes/${sceneIndex}/choice/validate`, (req, res, ctx) => {
          return res(ctx.json(mockValidationResult));
        })
      );

      const result = await sceneApiService.validateChoice(sessionId, sceneIndex, choiceId);

      expect(result).toEqual(mockValidationResult);
    });
  });
});

describe('ユーティリティ関数', () => {
  describe('getSceneFromChoiceId()', () => {
    it('正しい形式のchoiceIdからシーン番号を抽出する', () => {
      expect(getSceneFromChoiceId('choice_1_2')).toBe(1);
      expect(getSceneFromChoiceId('choice_3_4')).toBe(3);
    });

    it('不正な形式の場合nullを返す', () => {
      expect(getSceneFromChoiceId('invalid_format')).toBeNull();
      expect(getSceneFromChoiceId('choice_a_1')).toBeNull();
      expect(getSceneFromChoiceId('')).toBeNull();
    });
  });

  describe('getChoiceFromChoiceId()', () => {
    it('正しい形式のchoiceIdから選択肢番号を抽出する', () => {
      expect(getChoiceFromChoiceId('choice_1_2')).toBe(2);
      expect(getChoiceFromChoiceId('choice_3_4')).toBe(4);
    });

    it('不正な形式の場合nullを返す', () => {
      expect(getChoiceFromChoiceId('invalid_format')).toBeNull();
      expect(getChoiceFromChoiceId('choice_1_a')).toBeNull();
    });
  });

  describe('isValidChoiceId()', () => {
    it('正しい形式のchoiceIdを検証する', () => {
      expect(isValidChoiceId('choice_1_1')).toBe(true);
      expect(isValidChoiceId('choice_4_4')).toBe(true);
    });

    it('不正な形式を拒否する', () => {
      expect(isValidChoiceId('choice_0_1')).toBe(false); // シーン番号0は無効
      expect(isValidChoiceId('choice_5_1')).toBe(false); // シーン番号5は無効
      expect(isValidChoiceId('choice_1_0')).toBe(false); // 選択肢番号0は無効
      expect(isValidChoiceId('choice_1_5')).toBe(false); // 選択肢番号5は無効
      expect(isValidChoiceId('invalid')).toBe(false);
    });

    it('期待されるシーン番号をチェックする', () => {
      expect(isValidChoiceId('choice_2_1', 2)).toBe(true);
      expect(isValidChoiceId('choice_2_1', 1)).toBe(false);
    });
  });

  describe('generateChoiceId()', () => {
    it('正しい形式のchoiceIdを生成する', () => {
      expect(generateChoiceId(1, 2)).toBe('choice_1_2');
      expect(generateChoiceId(3, 4)).toBe('choice_3_4');
    });
  });

  describe('calculateProgressPercentage()', () => {
    it('進捗率を正しく計算する', () => {
      expect(calculateProgressPercentage(0, 4)).toBe(0);
      expect(calculateProgressPercentage(2, 4)).toBe(50);
      expect(calculateProgressPercentage(4, 4)).toBe(100);
    });

    it('100%を超えないようにする', () => {
      expect(calculateProgressPercentage(5, 4)).toBe(100);
    });
  });

  describe('canProceedToResult()', () => {
    it('全シーン完了時にtrueを返す', () => {
      expect(canProceedToResult(4, 4)).toBe(true);
      expect(canProceedToResult(5, 4)).toBe(true);
    });

    it('シーン未完了時にfalseを返す', () => {
      expect(canProceedToResult(3, 4)).toBe(false);
      expect(canProceedToResult(0, 4)).toBe(false);
    });
  });

  describe('getNextSceneIndex()', () => {
    it('次のシーンインデックスを返す', () => {
      expect(getNextSceneIndex(1, 4)).toBe(2);
      expect(getNextSceneIndex(3, 4)).toBe(4);
    });

    it('最終シーンの場合nullを返す', () => {
      expect(getNextSceneIndex(4, 4)).toBeNull();
      expect(getNextSceneIndex(5, 4)).toBeNull();
    });
  });

  describe('formatSceneText()', () => {
    it('シーン表示テキストを正しくフォーマットする', () => {
      expect(formatSceneText(1, 4)).toBe('シーン 1 / 4');
      expect(formatSceneText(3, 4)).toBe('シーン 3 / 4');
    });
  });

  describe('formatProgressText()', () => {
    it('進捗表示テキストを正しくフォーマットする', () => {
      expect(formatProgressText(0, 4)).toBe('0 / 4 完了');
      expect(formatProgressText(2, 4)).toBe('2 / 4 完了');
      expect(formatProgressText(4, 4)).toBe('4 / 4 完了');
    });
  });
});

describe('エラー判定関数', () => {
  describe('isSceneNotFoundError()', () => {
    it('セッション未発見エラーを正しく判定する', () => {
      const error = new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
      expect(isSceneNotFoundError(error)).toBe(true);
    });

    it('シーン未発見エラーを正しく判定する', () => {
      const error = new SessionAPIError('Scene not found', 404);
      expect(isSceneNotFoundError(error)).toBe(true);
    });

    it('他のエラーを正しく除外する', () => {
      const error = new SessionAPIError('Different error', 400, 'BAD_REQUEST');
      expect(isSceneNotFoundError(error)).toBe(false);
      
      const normalError = new Error('Normal error');
      expect(isSceneNotFoundError(normalError)).toBe(false);
    });
  });

  describe('isInvalidSceneError()', () => {
    it('無効なシーンエラーを正しく判定する', () => {
      const error1 = new SessionAPIError('Invalid scene', 400, 'INVALID_SCENE_INDEX');
      expect(isInvalidSceneError(error1)).toBe(true);
      
      const error2 = new SessionAPIError('Bad request', 400, 'BAD_REQUEST');
      expect(isInvalidSceneError(error2)).toBe(true);
    });

    it('他のエラーを正しく除外する', () => {
      const error = new SessionAPIError('Not found', 404, 'SESSION_NOT_FOUND');
      expect(isInvalidSceneError(error)).toBe(false);
    });
  });

  describe('isChoiceValidationError()', () => {
    it('選択肢バリデーションエラーを正しく判定する', () => {
      const error = new SessionAPIError('Validation failed', 400, 'VALIDATION_ERROR');
      expect(isChoiceValidationError(error)).toBe(true);
    });

    it('他のエラーを正しく除外する', () => {
      const error = new SessionAPIError('Bad request', 400, 'BAD_REQUEST');
      expect(isChoiceValidationError(error)).toBe(false);
    });
  });

  describe('isServiceUnavailableError()', () => {
    it('サービス利用不可エラーを正しく判定する', () => {
      const error = new SessionAPIError('Service unavailable', 503, 'LLM_SERVICE_UNAVAILABLE');
      expect(isServiceUnavailableError(error)).toBe(true);
    });

    it('他のエラーを正しく除外する', () => {
      const error = new SessionAPIError('Not found', 404, 'SESSION_NOT_FOUND');
      expect(isServiceUnavailableError(error)).toBe(false);
    });
  });
});

describe('getSceneErrorMessage()', () => {
  it('セッション/シーン未発見エラーのメッセージを返す', () => {
    const error = new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('セッションまたはシーンが見つかりません。最初からやり直してください。');
  });

  it('無効なシーンエラーのメッセージを返す', () => {
    const error = new SessionAPIError('Invalid scene', 400, 'INVALID_SCENE_INDEX');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('このシーンにはアクセスできません。前のシーンを完了してください。');
  });

  it('選択肢バリデーションエラーのメッセージを返す', () => {
    const error = new SessionAPIError('Invalid choice', 400, 'VALIDATION_ERROR');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('選択肢が無効です。有効な選択肢を選んでください。');
  });

  it('サービス利用不可エラーのメッセージを返す', () => {
    const error = new SessionAPIError('Service unavailable', 503, 'LLM_SERVICE_UNAVAILABLE');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('サービスが一時的に利用できません。しばらく待ってから再試行してください。');
  });

  it('SessionAPIErrorの一般的なメッセージを返す', () => {
    const error = new SessionAPIError('Custom error message', 500, 'UNKNOWN_ERROR');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('Custom error message');
  });

  it('一般的なエラーの場合はデフォルトメッセージを返す', () => {
    const error = new Error('Generic error');
    const message = getSceneErrorMessage(error);
    expect(message).toBe('エラーが発生しました。再試行してください。');
  });

  it('未知のエラータイプの場合はデフォルトメッセージを返す', () => {
    const message = getSceneErrorMessage('string error');
    expect(message).toBe('エラーが発生しました。再試行してください。');
  });
});

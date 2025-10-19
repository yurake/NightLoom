/**
 * Session Cleanup Utilities Tests
 */

import {
  clearAllSessionData,
  clearSessionById,
  clearResultData,
  resetMemoryState,
  replaceHistoryForSessionIsolation,
  performRestartCleanup,
  validateSessionState,
  debugSessionState,
  STORAGE_KEYS
} from '../../app/utils/session-cleanup';

// LocalStorage モック
const localStorageMock: {
  store: Record<string, string>;
  getItem: jest.MockedFunction<(key: string) => string | null>;
  setItem: jest.MockedFunction<(key: string, value: string) => void>;
  removeItem: jest.MockedFunction<(key: string) => void>;
  clear: jest.MockedFunction<() => void>;
} = {
  store: {} as Record<string, string>,
  getItem: jest.fn((key: string): string | null => localStorageMock.store[key] || null),
  setItem: jest.fn((key: string, value: string): void => {
    localStorageMock.store[key] = value;
  }),
  removeItem: jest.fn((key: string): void => {
    delete localStorageMock.store[key];
  }),
  clear: jest.fn((): void => {
    localStorageMock.store = {};
  })
};

// SessionStorage モック
const sessionStorageMock = {
  clear: jest.fn()
};

// Window履歴モック
const historyMock = {
  replaceState: jest.fn()
};

describe('Session Cleanup Utilities', () => {
  beforeEach(() => {
    // モックをリセット
    localStorageMock.store = {};
    jest.clearAllMocks();
    
    // グローバルオブジェクトにモックを設定
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
    
    Object.defineProperty(window, 'sessionStorage', {
      value: sessionStorageMock,
      writable: true
    });
    
    Object.defineProperty(window, 'history', {
      value: historyMock,
      writable: true
    });

    // console.log/warn をモック
    jest.spyOn(console, 'log').mockImplementation();
    jest.spyOn(console, 'warn').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('clearAllSessionData', () => {
    it('LocalStorageからすべてのセッションキーを削除する', () => {
      // Setup: データを事前に設定
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorageMock.store[key] = 'test-value';
      });

      // Execute
      clearAllSessionData();

      // Assert: すべてのキーが削除されている
      Object.values(STORAGE_KEYS).forEach(key => {
        expect(localStorageMock.removeItem).toHaveBeenCalledWith(key);
      });
      expect(sessionStorageMock.clear).toHaveBeenCalled();
    });

    it('LocalStorageアクセス失敗時に警告ログを出力する', () => {
      // Setup: LocalStorageでエラーを発生させる
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      // Execute
      clearAllSessionData();

      // Assert: エラーが適切にハンドリングされる
      expect(console.warn).toHaveBeenCalledWith(
        'Failed to clear session ',
        expect.any(Error)
      );
    });
  });

  describe('clearSessionById', () => {
    it('指定されたセッションIDが現在のセッションと一致する場合にクリアする', () => {
      // Setup
      const testSessionId = 'test-session-123';
      localStorageMock.store[STORAGE_KEYS.SESSION_ID] = testSessionId;

      // Execute
      clearSessionById(testSessionId);

      // Assert: セッションデータがクリアされる
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.SESSION_ID);
    });

    it('セッションIDが一致しない場合はクリアしない', () => {
      // Setup
      localStorageMock.store[STORAGE_KEYS.SESSION_ID] = 'different-session';

      // Execute
      clearSessionById('test-session-123');

      // Assert: 削除処理が呼ばれない
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(console.log).toHaveBeenCalledWith(
        'Session ID mismatch, skipping cleanup: test-session-123'
      );
    });
  });

  describe('clearResultData', () => {
    it('結果データのみを削除する', () => {
      // Setup
      localStorageMock.store[STORAGE_KEYS.RESULT_DATA] = 'test-result';
      localStorageMock.store[STORAGE_KEYS.SESSION_ID] = 'test-session';

      // Execute
      clearResultData();

      // Assert: 結果データのみが削除される
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.RESULT_DATA);
      expect(localStorageMock.removeItem).not.toHaveBeenCalledWith(STORAGE_KEYS.SESSION_ID);
    });
  });

  describe('resetMemoryState', () => {
    it('カスタムイベントを発火する', () => {
      // Setup: dispatchEventをモック
      const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent').mockImplementation();

      // Execute
      resetMemoryState();

      // Assert: 適切なイベントが発火される
      expect(dispatchEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'nightloom:session-reset',
          detail: expect.objectContaining({
            timestamp: expect.any(Number)
          })
        })
      );
    });
  });

  describe('replaceHistoryForSessionIsolation', () => {
    it('履歴を置換する', () => {
      // Execute
      replaceHistoryForSessionIsolation();

      // Assert: 履歴が適切に置換される（pathnameは現在のものが使用される）
      expect(historyMock.replaceState).toHaveBeenCalledWith(
        { nightloom: true, timestamp: expect.any(Number) },
        '',
        expect.any(String) // pathnameは何らかの文字列であることを確認
      );
    });

    it('履歴操作失敗時に警告ログを出力する', () => {
      // Setup: history.replaceStateでエラーを発生させる
      historyMock.replaceState.mockImplementation(() => {
        throw new Error('History API error');
      });

      // Execute
      replaceHistoryForSessionIsolation();

      // Assert: エラーが適切にハンドリングされる
      expect(console.warn).toHaveBeenCalledWith(
        'Failed to replace history:',
        expect.any(Error)
      );
    });
  });

  describe('performRestartCleanup', () => {
    it('包括的なクリーンアップを実行する', () => {
      // Setup: 各関数をスパイ
      const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent').mockImplementation();

      // Execute
      performRestartCleanup();

      // Assert: すべてのクリーンアップ処理が実行される
      expect(localStorageMock.removeItem).toHaveBeenCalled();
      expect(dispatchEventSpy).toHaveBeenCalled();
      expect(historyMock.replaceState).toHaveBeenCalled();
      expect(console.log).toHaveBeenCalledWith('Starting comprehensive restart cleanup...');
      expect(console.log).toHaveBeenCalledWith('Restart cleanup completed');
    });
  });

  describe('validateSessionState', () => {
    it('有効なセッション状態を返す', () => {
      // Setup
      localStorageMock.store[STORAGE_KEYS.SESSION_ID] = 'test-session';
      localStorageMock.store[STORAGE_KEYS.RESULT_DATA] = 'test-result';

      // Execute
      const result = validateSessionState();

      // Assert
      expect(result).toEqual({
        isValid: true,
        sessionId: 'test-session',
        hasResultData: true
      });
    });

    it('無効なセッション状態を返す', () => {
      // Setup: セッションIDなし

      // Execute
      const result = validateSessionState();

      // Assert
      expect(result).toEqual({
        isValid: false,
        sessionId: null,
        hasResultData: false
      });
    });

    it('LocalStorage読み取り失敗時にフォールバック値を返す', () => {
      // Setup: getItemでエラーを発生させる
      const originalGetItem = localStorageMock.getItem;
      localStorageMock.getItem.mockImplementation((key: string): string | null => {
        throw new Error('localStorage error');
      });

      // Execute
      const result = validateSessionState();

      // Assert: フォールバック値が返される
      expect(result).toEqual({
        isValid: false,
        sessionId: null,
        hasResultData: false
      });
      expect(console.warn).toHaveBeenCalled();

      // Cleanup: モックを元に戻す
      localStorageMock.getItem.mockRestore();
      localStorageMock.getItem = originalGetItem;
    });
  });

  describe('debugSessionState', () => {
    it('開発環境でデバッグ情報を出力する', () => {
      // Setup: 開発環境を設定
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true
      });
      
      const consoleGroupSpy = jest.spyOn(console, 'group').mockImplementation();
      const consoleGroupEndSpy = jest.spyOn(console, 'groupEnd').mockImplementation();

      // Setup: テスト用データ
      localStorageMock.store[STORAGE_KEYS.SESSION_ID] = 'test-session';
      
      // sessionStorageのkeysメソッドをモック
      const mockSessionStorage = {
        ...sessionStorageMock,
        keys: ['test-key-1', 'test-key-2']
      };
      Object.defineProperty(window, 'sessionStorage', {
        value: mockSessionStorage,
        writable: true
      });

      // Execute
      debugSessionState();

      // Assert: デバッグ出力が実行される
      expect(consoleGroupSpy).toHaveBeenCalledWith('🔍 NightLoom Session Debug');
      expect(console.log).toHaveBeenCalledWith('Session State:', expect.any(Object));
      expect(console.log).toHaveBeenCalledWith('LocalStorage Data:', expect.any(Object));
      expect(consoleGroupEndSpy).toHaveBeenCalled();

      // Cleanup
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true
      });
    });

    it('本番環境では何も出力しない', () => {
      // Setup: 本番環境を設定
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true
      });
      
      const consoleGroupSpy = jest.spyOn(console, 'group').mockImplementation();

      // Execute
      debugSessionState();

      // Assert: デバッグ出力されない
      expect(consoleGroupSpy).not.toHaveBeenCalled();

      // Cleanup
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true
      });
    });
  });
});

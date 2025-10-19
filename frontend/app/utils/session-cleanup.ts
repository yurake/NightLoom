/**
 * Session Cleanup Utilities
 * 
 * セッションデータのクリーンアップを行うユーティリティ関数群
 * LocalStorage、セッション状態、結果データの管理
 */

/**
 * LocalStorageのキー定数
 */
export const STORAGE_KEYS = {
  SESSION_ID: 'nightloom_session_id',
  SESSION_STATE: 'nightloom_session_state', 
  RESULT_DATA: 'nightloom_result_data',
  USER_PROGRESS: 'nightloom_user_progress',
} as const;

/**
 * セッション関連データの完全クリーンアップ
 * 新しい診断開始時に呼び出される
 */
export function clearAllSessionData(): void {
  try {
    // LocalStorageからセッション関連データを削除
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });

    // SessionStorageもクリア
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.clear();
    }

    console.log('Session data cleared successfully');
  } catch (error) {
    console.warn('Failed to clear session ', error);
  }
}

/**
 * 特定のセッションIDのデータをクリーンアップ
 * @param sessionId クリーンアップ対象のセッションID
 */
export function clearSessionById(sessionId: string): void {
  try {
    const currentSessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
    
    // 指定されたセッションIDが現在のセッションと一致する場合のみクリア
    if (currentSessionId === sessionId) {
      clearAllSessionData();
      console.log(`Session ${sessionId} cleared successfully`);
    } else {
      console.log(`Session ID mismatch, skipping cleanup: ${sessionId}`);
    }
  } catch (error) {
    console.warn('Failed to clear session by ID:', error);
  }
}

/**
 * 結果データのみをクリーンアップ
 * セッションIDは保持しつつ、結果キャッシュのみ削除
 */
export function clearResultData(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.RESULT_DATA);
    console.log('Result data cleared successfully');
  } catch (error) {
    console.warn('Failed to clear result ', error);
  }
}

/**
 * メモリ内の状態をリセット
 * Reactの状態管理やコンテキストのリセットに使用
 */
export function resetMemoryState(): void {
  // Window オブジェクトにアタッチされている可能性のある状態をクリア
  if (typeof window !== 'undefined') {
    // カスタムイベントを発火してReactコンポーネントに通知
    window.dispatchEvent(new CustomEvent('nightloom:session-reset', {
      detail: { timestamp: Date.now() }
    }));
  }
}

/**
 * ブラウザバック無効化のための履歴操作
 * セッション独立性を保証
 */
export function replaceHistoryForSessionIsolation(): void {
  if (typeof window !== 'undefined' && window.history) {
    try {
      // 現在のURLを履歴に置換（戻るボタンでセッションが混在しないように）
      window.history.replaceState(
        { nightloom: true, timestamp: Date.now() },
        '',
        window.location.pathname
      );
      console.log('History replaced for session isolation');
    } catch (error) {
      console.warn('Failed to replace history:', error);
    }
  }
}

/**
 * 診断再開始時の包括的クリーンアップ
 * 「もう一度診断する」ボタンから呼び出される
 */
export function performRestartCleanup(): void {
  console.log('Starting comprehensive restart cleanup...');
  
  // 1. セッションデータクリア
  clearAllSessionData();
  
  // 2. メモリ状態リセット
  resetMemoryState();
  
  // 3. 履歴操作
  replaceHistoryForSessionIsolation();
  
  console.log('Restart cleanup completed');
}

/**
 * セッション状態の検証
 * 現在のセッションが有効かどうかをチェック
 */
export function validateSessionState(): {
  isValid: boolean;
  sessionId: string | null;
  hasResultData: boolean;
} {
  try {
    const sessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
    const resultData = localStorage.getItem(STORAGE_KEYS.RESULT_DATA);
    
    return {
      isValid: Boolean(sessionId),
      sessionId,
      hasResultData: Boolean(resultData)
    };
  } catch (error) {
    console.warn('Failed to validate session state:', error);
    return {
      isValid: false,
      sessionId: null,
      hasResultData: false
    };
  }
}

/**
 * デバッグ用: 現在のセッション状態を出力
 */
export function debugSessionState(): void {
  if (process.env.NODE_ENV === 'development') {
    const state = validateSessionState();
    const allData = Object.fromEntries(
      Object.values(STORAGE_KEYS).map(key => [
        key,
        localStorage.getItem(key)
      ])
    );
    
    console.group('🔍 NightLoom Session Debug');
    console.log('Session State:', state);
    console.log('LocalStorage Data:', allData);
    console.log('SessionStorage Keys:', Object.keys(sessionStorage));
    console.groupEnd();
  }
}

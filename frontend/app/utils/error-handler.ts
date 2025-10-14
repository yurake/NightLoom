/**
 * エラーハンドリングユーティリティ
 *
 * API エラーレスポンスの処理とフォールバックロジック
 */

import type { ErrorResponse, ErrorCode, ClientErrorCode } from '@/app/types/result';

/**
 * API エラーを表すクラス
 */
export class ApiError extends Error {
  constructor(
    public code: ErrorCode | ClientErrorCode,
    message: string,
    public sessionId?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * HTTP レスポンスからエラーを解析
 */
export async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const errorData = await response.json() as ErrorResponse;

    if (errorData.error && errorData.error.code) {
      return new ApiError(
        errorData.error.code,
        errorData.error.message,
        errorData.sessionId,
        errorData.error.details
      );
    }

    // エラーレスポンスが不正な場合
    return new ApiError(
      'NETWORK_ERROR',
      `HTTP Error: ${response.status} ${response.statusText}`
    );
  } catch {
    // JSON パースエラー
    return new ApiError(
      'PARSE_ERROR',
      `Failed to parse error response: ${response.status}`
    );
  }
}

/**
 * ネットワークエラーを処理
 */
export function handleNetworkError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (error instanceof TypeError && error.message.includes('fetch')) {
    return new ApiError('NETWORK_ERROR', 'ネットワーク接続エラーが発生しました');
  }

  if (error instanceof Error) {
    return new ApiError('NETWORK_ERROR', error.message);
  }

  return new ApiError('NETWORK_ERROR', '不明なエラーが発生しました');
}

/**
 * タイムアウトエラーを作成
 */
export function createTimeoutError(timeoutMs: number): ApiError {
  return new ApiError(
    'TIMEOUT_ERROR',
    `リクエストがタイムアウトしました (${timeoutMs}ms)`
  );
}

/**
 * エラーコードに対応するユーザー向けメッセージを取得
 */
export function getErrorMessage(code: ErrorCode | ClientErrorCode): string {
  const messages: Record<ErrorCode | ClientErrorCode, string> = {
    SESSION_NOT_FOUND: 'セッションが見つかりません',
    SESSION_NOT_COMPLETED: '診断が完了していません',
    TYPE_GEN_FAILED: '結果を生成しています...',
    INVALID_SESSION_STATE: 'セッション状態が不正です',
    NETWORK_ERROR: '接続エラーが発生しました',
    TIMEOUT_ERROR: 'リクエストがタイムアウトしました',
    PARSE_ERROR: 'レスポンスの解析に失敗しました',
    VALIDATION_ERROR: 'データの検証に失敗しました',
  };

  return messages[code] || '予期しないエラーが発生しました';
}

/**
 * エラーに対するアクション（ボタンテキスト）を取得
 */
export function getErrorAction(code: ErrorCode | ClientErrorCode): {
  primary?: string;
  secondary?: string;
} {
  switch (code) {
    case 'SESSION_NOT_FOUND':
      return { primary: '初期画面へ戻る' };
    case 'SESSION_NOT_COMPLETED':
      return { primary: '診断を続ける' };
    case 'TYPE_GEN_FAILED':
      // プリセットタイプを透明的に使用するため、ユーザーには通常表示
      return {};
    case 'NETWORK_ERROR':
    case 'TIMEOUT_ERROR':
      return { primary: '再試行', secondary: '初期画面へ戻る' };
    case 'PARSE_ERROR':
    case 'VALIDATION_ERROR':
      return { primary: '再読み込み', secondary: '初期画面へ戻る' };
    default:
      return { primary: '初期画面へ戻る' };
  }
}

/**
 * エラーコードに基づいてリダイレクト先URLを取得
 */
export function getErrorRedirectUrl(
  code: ErrorCode | ClientErrorCode,
  sessionId?: string
): string | null {
  switch (code) {
    case 'SESSION_NOT_FOUND':
      // 3秒後に自動リダイレクト
      return '/';
    case 'SESSION_NOT_COMPLETED':
      // 現在のシーン画面へ
      return sessionId ? `/play/${sessionId}` : '/';
    case 'TYPE_GEN_FAILED':
      // リダイレクトなし（プリセットタイプで続行）
      return null;
    default:
      return null;
  }
}

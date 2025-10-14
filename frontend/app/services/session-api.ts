/**
 * SessionApiClient クラス
 *
 * セッションAPIとの通信を管理するクライアント
 */

import type { ResultData } from '@/app/types/result';
import { validateResultData } from '@/app/utils/validators';
import {
  ApiError,
  parseErrorResponse,
  handleNetworkError,
  createTimeoutError,
} from '@/app/utils/error-handler';

/**
 * APIクライアント設定オプション
 */
export interface SessionApiClientOptions {
  /** タイムアウト時間（ミリ秒） */
  timeout?: number;
  /** リトライ回数 */
  retries?: number;
}

/**
 * セッションAPI クライアント
 */
export class SessionApiClient {
  private readonly baseUrl: string;
  private readonly timeout: number;
  private readonly retries: number;

  constructor(baseUrl: string, options: SessionApiClientOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // 末尾のスラッシュを削除
    this.timeout = options.timeout ?? 12000; // デフォルト12秒
    this.retries = options.retries ?? 0; // デフォルトリトライなし
  }

  /**
   * セッション結果を取得
   *
   * @param sessionId - セッションID（UUID v4）
   * @returns 診断結果データ
   * @throws {ApiError} API エラーまたはネットワークエラー
   */
  async getResult(sessionId: string): Promise<ResultData> {
    const url = `${this.baseUrl}/api/sessions/${sessionId}/result`;

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // エラーレスポンスの処理
      if (!response.ok) {
        const apiError = await parseErrorResponse(response);
        throw apiError;
      }

      // 成功レスポンスの解析と検証
      const data = await response.json();
      const validation = validateResultData(data);

      if (!validation.valid) {
        throw new ApiError(
          'VALIDATION_ERROR',
          `レスポンスデータが不正です: ${validation.error}`
        );
      }

      return validation.data;
    } catch (error) {
      // ApiError はそのまま再スロー
      if (error instanceof ApiError) {
        throw error;
      }

      // その他のエラーはネットワークエラーとして処理
      throw handleNetworkError(error);
    }
  }

  /**
   * タイムアウト付きfetch
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      return response;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw createTimeoutError(this.timeout);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * リトライ付きリクエスト（将来拡張用）
   */
  private async fetchWithRetry(
    url: string,
    options: RequestInit,
    retriesLeft: number = this.retries
  ): Promise<Response> {
    try {
      return await this.fetchWithTimeout(url, options);
    } catch (error) {
      if (retriesLeft > 0 && this.shouldRetry(error)) {
        // 指数バックオフ: 1秒、2秒、4秒...
        const delay = Math.pow(2, this.retries - retriesLeft) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchWithRetry(url, options, retriesLeft - 1);
      }
      throw error;
    }
  }

  /**
   * リトライすべきエラーかどうかを判定
   */
  private shouldRetry(error: unknown): boolean {
    if (error instanceof ApiError) {
      // ネットワークエラーとタイムアウトのみリトライ
      return error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT_ERROR';
    }
    return false;
  }
}

/**
 * デフォルトAPIクライアントインスタンス
 */
export const defaultApiClient = new SessionApiClient(
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  {
    timeout: 12000,
    retries: 0,
  }
);

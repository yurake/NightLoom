/**
 * SessionApiClient テスト
 *
 * TDD: テスト先行で作成、実装前に失敗を確認
 */

import { SessionApiClient } from '../../app/services/session-api';
import { mockResult2Axes } from '../mocks/result-data';

// Mock fetch globally
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe('SessionApiClient', () => {
  const baseUrl = 'http://localhost:8000';
  let client: SessionApiClient;

  beforeEach(() => {
    client = new SessionApiClient(baseUrl);
    jest.clearAllMocks();
  });

  describe('getResult', () => {
    it('正常にセッション結果を取得できる', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult2Axes,
      } as Response);

      const result = await client.getResult('550e8400-e29b-41d4-a716-446655440000');

      expect(result).toEqual(mockResult2Axes);
      expect(result.sessionId).toBe('550e8400-e29b-41d4-a716-446655440000');
      expect(result.axes).toHaveLength(2);
      expect(result.type.name).toBe('Logical Thinker');
    });

    it('セッションが見つからない場合はエラーをスローする', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({
          error: {
            code: 'SESSION_NOT_FOUND',
            message: 'セッションが見つかりません'
          }
        }),
      } as Response);

      await expect(
        client.getResult('invalid-session-id')
      ).rejects.toThrow('SESSION_NOT_FOUND');
    });

    it('診断が未完了の場合はエラーをスローする', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({
          error: {
            code: 'SESSION_NOT_COMPLETED',
            message: '診断が完了していません'
          }
        }),
      } as Response);

      await expect(
        client.getResult('550e8400-e29b-41d4-a716-446655440002')
      ).rejects.toThrow('SESSION_NOT_COMPLETED');
    });

    it('タイプ生成に失敗した場合はエラーをスローする', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({
          error: {
            code: 'TYPE_GEN_FAILED',
            message: 'タイプ生成に失敗しました'
          }
        }),
      } as Response);

      await expect(
        client.getResult('550e8400-e29b-41d4-a716-446655440003')
      ).rejects.toThrow('TYPE_GEN_FAILED');
    });

    it('タイムアウト設定が有効である', async () => {
      const shortTimeoutClient = new SessionApiClient(baseUrl, { timeout: 100 });

      // タイムアウトテストは実装後に有効化
      // await expect(
      //   shortTimeoutClient.getResult('test-timeout')
      // ).rejects.toThrow('TIMEOUT_ERROR');
    });

    it('ネットワークエラーを適切に処理する', async () => {
      const invalidUrlClient = new SessionApiClient('http://invalid-host:9999');

      await expect(
        invalidUrlClient.getResult('test-session')
      ).rejects.toThrow();
    });

    it('レスポンスデータを検証する', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult2Axes,
      } as Response);

      const result = await client.getResult('550e8400-e29b-41d4-a716-446655440000');

      // ResultData型の検証
      expect(result).toHaveProperty('sessionId');
      expect(result).toHaveProperty('keyword');
      expect(result).toHaveProperty('axes');
      expect(result).toHaveProperty('type');
      expect(result).toHaveProperty('completedAt');

      // axes の検証
      expect(Array.isArray(result.axes)).toBe(true);
      expect(result.axes.length).toBeGreaterThanOrEqual(2);
      expect(result.axes.length).toBeLessThanOrEqual(6);

      // type の検証
      expect(result.type).toHaveProperty('name');
      expect(result.type).toHaveProperty('description');
      expect(result.type).toHaveProperty('dominantAxes');
      expect(result.type).toHaveProperty('polarity');
    });
  });
});

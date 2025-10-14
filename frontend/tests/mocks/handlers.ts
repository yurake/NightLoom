/**
 * NightLoom 結果画面 MSW ハンドラー
 *
 * Mock Service Worker (MSW) を使用したAPI モックハンドラー定義
 */

import { http, HttpResponse } from 'msw';
import {
  mockResult2Axes,
  mockResult6Axes,
  mockErrorNotFound,
  mockErrorNotCompleted,
  mockErrorTypeGenFailed
} from './result-data';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const handlers = [
  // 成功: 2軸結果取得
  http.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440000/result`, () => {
    return HttpResponse.json(mockResult2Axes);
  }),

  // 成功: 6軸結果取得
  http.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440001/result`, () => {
    return HttpResponse.json(mockResult6Axes);
  }),

  // エラー: セッション未存在 (404)
  http.get(`${BASE_URL}/api/sessions/invalid-session-id/result`, () => {
    return HttpResponse.json(mockErrorNotFound, { status: 404 });
  }),

  // エラー: 診断未完了 (400)
  http.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440002/result`, () => {
    return HttpResponse.json(mockErrorNotCompleted, { status: 400 });
  }),

  // エラー: タイプ生成失敗 (500)
  http.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440003/result`, () => {
    return HttpResponse.json(mockErrorTypeGenFailed, { status: 500 });
  }),

  // デフォルトハンドラー: 任意のセッションID
  http.get(`${BASE_URL}/api/sessions/:sessionId/result`, ({ params }) => {
    const { sessionId } = params;

    // テストセッションIDの場合は2軸データを返す
    if (typeof sessionId === 'string' && sessionId.startsWith('test-')) {
      return HttpResponse.json(mockResult2Axes);
    }

    // それ以外は404エラー
    return HttpResponse.json(mockErrorNotFound, { status: 404 });
  }),
];

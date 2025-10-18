/**
 * NightLoom 結果画面 MSW ハンドラー
 *
 * Mock Service Worker (MSW) を使用したAPI モックハンドラー定義
 */

import { rest } from 'msw';
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
  rest.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440000/result`, (req, res, ctx) => {
    return res(ctx.json(mockResult2Axes));
  }),

  // 成功: 6軸結果取得
  rest.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440001/result`, (req, res, ctx) => {
    return res(ctx.json(mockResult6Axes));
  }),

  // エラー: セッション未存在 (404)
  rest.get(`${BASE_URL}/api/sessions/invalid-session-id/result`, (req, res, ctx) => {
    return res(ctx.status(404), ctx.json(mockErrorNotFound));
  }),

  // エラー: 診断未完了 (400)
  rest.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440002/result`, (req, res, ctx) => {
    return res(ctx.status(400), ctx.json(mockErrorNotCompleted));
  }),

  // エラー: タイプ生成失敗 (500)
  rest.get(`${BASE_URL}/api/sessions/550e8400-e29b-41d4-a716-446655440003/result`, (req, res, ctx) => {
    return res(ctx.status(500), ctx.json(mockErrorTypeGenFailed));
  }),

  // デフォルトハンドラー: 任意のセッションID
  rest.get(`${BASE_URL}/api/sessions/:sessionId/result`, (req, res, ctx) => {
    const { sessionId } = req.params;

    // テストセッションIDの場合は2軸データを返す
    if (typeof sessionId === 'string' && sessionId.startsWith('test-')) {
      return res(ctx.json(mockResult2Axes));
    }

    // それ以外は404エラー
    return res(ctx.status(404), ctx.json(mockErrorNotFound));
  }),
];

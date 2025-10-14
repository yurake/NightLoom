/**
 * NightLoom 結果画面 モックデータ
 *
 * テストで使用するモックデータを提供します。
 */

import type { ResultData } from '@/app/types/result';

/**
 * 基本的な2軸結果のモックデータ
 */
export const mockResult2Axes: ResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  keyword: 'アート',
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考と感情的判断のバランス',
      direction: '論理的 ⟷ 感情的',
      score: 75.5,
      rawScore: 2.1
    },
    {
      id: 'axis_2',
      name: '社交性',
      description: '集団行動と個人行動の指向性',
      direction: '社交的 ⟷ 内省的',
      score: 42.3,
      rawScore: -0.8
    }
  ],
  type: {
    name: 'Logical Thinker',
    description: '論理的思考を重視し、個人での内省を好む傾向があります。',
    dominantAxes: ['axis_1', 'axis_2'],
    polarity: 'Hi-Lo'
  },
  completedAt: '2025-10-14T13:15:00Z'
};

/**
 * 6軸結果のモックデータ
 */
export const mockResult6Axes: ResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440001',
  keyword: '冒険',
  axes: [
    {
      id: 'axis_1',
      name: '探索性',
      description: '新しい経験への開放性',
      direction: '探索的 ⟷ 慎重的',
      score: 85.2,
      rawScore: 3.5
    },
    {
      id: 'axis_2',
      name: '計画性',
      description: '行動の計画と準備',
      direction: '計画的 ⟷ 直感的',
      score: 35.7,
      rawScore: -1.4
    },
    {
      id: 'axis_3',
      name: '協調性',
      description: 'チームワークと協力',
      direction: '協調的 ⟷ 独立的',
      score: 62.1,
      rawScore: 1.2
    },
    {
      id: 'axis_4',
      name: '分析性',
      description: '情報の分析と検証',
      direction: '分析的 ⟷ 直感的',
      score: 48.9,
      rawScore: -0.1
    },
    {
      id: 'axis_5',
      name: '表現性',
      description: '自己表現と創造性',
      direction: '表現的 ⟷ 内省的',
      score: 71.4,
      rawScore: 1.9
    },
    {
      id: 'axis_6',
      name: '安定性',
      description: 'リスク回避と安定志向',
      direction: '安定的 ⟷ 冒険的',
      score: 28.3,
      rawScore: -2.2
    }
  ],
  type: {
    name: 'Creative Explorer',
    description: '創造性と探索心を兼ね備え、新しい挑戦を好む傾向があります。',
    dominantAxes: ['axis_1', 'axis_6'],
    polarity: 'Hi-Lo'
  },
  completedAt: '2025-10-14T13:16:00Z'
};

/**
 * エラー状態のモックデータ
 */
export const mockErrorNotFound = {
  error: {
    code: 'SESSION_NOT_FOUND' as const,
    message: 'セッションが見つかりません',
  },
  sessionId: 'invalid-session-id'
};

export const mockErrorNotCompleted = {
  error: {
    code: 'SESSION_NOT_COMPLETED' as const,
    message: '診断が完了していません',
  },
  sessionId: '550e8400-e29b-41d4-a716-446655440002'
};

export const mockErrorTypeGenFailed = {
  error: {
    code: 'TYPE_GEN_FAILED' as const,
    message: 'タイプ生成に失敗しました',
  },
  sessionId: '550e8400-e29b-41d4-a716-446655440003'
};

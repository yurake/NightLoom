/**
 * NightLoom 結果画面 型定義
 *
 * このファイルはフロントエンドで使用する結果画面関連の型定義を
 * 一元管理します。設計文書とは独立して実装を維持します。
 */

// ===== Core Data Types =====

/**
 * 診断結果データ
 * セッション完了後の全結果情報を含む最上位エンティティ
 */
export interface ResultData {
  /** セッション識別子（UUID v4） */
  sessionId: string;
  
  /** 初期選択キーワード */
  keyword: string;
  
  /** 評価軸スコア配列（2-6軸） */
  axes: AxisScore[];
  
  /** タイプ分類結果 */
  type: TypeResult;
  
  /** 診断完了時刻（ISO 8601） */
  completedAt: string;
  
  /** UIテーマ識別子（将来拡張） */
  themeId?: ThemeId;
}

/**
 * 評価軸スコア
 * 個別評価軸のスコア情報とメタデータ
 */
export interface AxisScore {
  /** 軸識別子（axis_1, axis_2, ...） */
  id: string;
  
  /** 軸名称（日本語） */
  name: string;
  
  /** 軸の詳細説明 */
  description: string;
  
  /** 方向性表示（例：「論理的 ⟷ 感情的」） */
  direction: string;
  
  /** 正規化後スコア（0-100、小数第1位まで） */
  score: number;
  
  /** 正規化前スコア（理論範囲-5.0〜5.0） */
  rawScore: number;
}

/**
 * タイプ分類結果
 * 動的生成されたユーザータイプ分類情報
 */
export interface TypeResult {
  /** タイプ名（英語1-2語、最大14文字） */
  name: string;
  
  /** タイプ説明（50文字以内） */
  description: string;
  
  /** 主軸ID配列（2要素固定） */
  dominantAxes: [string, string];
  
  /** 極性パターン（主軸2つの高低組み合わせ） */
  polarity: PolarityPattern;
}

/**
 * 極性パターン列挙型
 * 主軸2つのスコア水準組み合わせ
 */
export type PolarityPattern = 
  | 'Hi-Hi'   // 両軸高スコア
  | 'Hi-Lo'   // 軸A高・軸B低
  | 'Lo-Hi'   // 軸A低・軸B高
  | 'Lo-Lo'   // 両軸低スコア
  | 'Hi-Mid'  // 軸A高・軸B中間
  | 'Lo-Mid'  // 軸A低・軸B中間
  | 'Mid-Hi'  // 軸A中間・軸B高
  | 'Mid-Lo'  // 軸A中間・軸B低
  | 'Mid-Mid'; // 両軸中間

/**
 * UIテーマ識別子（将来拡張用）
 */
export type ThemeId = 'serene' | 'adventure' | 'focus' | 'fallback';

// ===== Error Types =====

/**
 * APIエラーレスポンス
 */
export interface ErrorResponse {
  /** エラー情報 */
  error: {
    /** エラーコード */
    code: ErrorCode;
    
    /** エラーメッセージ（日本語） */
    message: string;
    
    /** エラー詳細情報（任意） */
    details?: Record<string, unknown>;
  };
  
  /** 関連セッションID（参照用、任意） */
  sessionId?: string;
}

/**
 * エラーコード列挙型
 */
export type ErrorCode = 
  | 'SESSION_NOT_FOUND'      // セッション未存在
  | 'SESSION_NOT_COMPLETED'  // 診断未完了
  | 'TYPE_GEN_FAILED'        // タイプ生成失敗
  | 'INVALID_SESSION_STATE'; // セッション状態不正

// ===== Client-side Types =====

/**
 * クライアントサイドエラーコード
 * API呼び出し・ネットワーク関連エラー
 */
export type ClientErrorCode = 
  | 'NETWORK_ERROR'    // ネットワークエラー
  | 'TIMEOUT_ERROR'    // タイムアウト
  | 'PARSE_ERROR'      // レスポンス解析エラー
  | 'VALIDATION_ERROR'; // データ検証エラー

/**
 * クライアント拡張エラーレスポンス
 */
export interface ClientErrorResponse {
  error: {
    code: ErrorCode | ClientErrorCode;
    message: string;
    details?: Record<string, unknown>;
  };
  sessionId?: string;
}

// ===== API Request/Response Types =====

/**
 * 結果取得リクエストパラメータ
 */
export interface GetResultRequest {
  /** セッションID（パスパラメータ） */
  sessionId: string;
}

/**
 * 結果取得レスポンス
 * ResultDataと同一構造
 */
export type GetResultResponse = ResultData;

// ===== Validation Types =====

/**
 * 軸ID検証用正規表現パターン
 */
export const AXIS_ID_PATTERN = /^axis_\d+$/;

/**
 * セッションID検証用正規表現パターン（UUID v4）
 */
export const SESSION_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * タイプ名検証用正規表現パターン（英語1-2語）
 */
export const TYPE_NAME_PATTERN = /^[A-Z][a-z]+( [A-Z][a-z]+)?$/;

/**
 * 方向性表示検証用正規表現パターン（⟷区切り）
 */
export const DIRECTION_PATTERN = /.+ ⟷ .+/;

// ===== Type Guards =====

/**
 * ResultData型ガード
 */
export const isResultData = (obj: unknown): obj is ResultData => {
  if (!obj || typeof obj !== 'object') return false;
  
  const result = obj as ResultData;
  
  return (
    typeof result.sessionId === 'string' &&
    SESSION_ID_PATTERN.test(result.sessionId) &&
    typeof result.keyword === 'string' &&
    result.keyword.length >= 1 &&
    result.keyword.length <= 20 &&
    Array.isArray(result.axes) &&
    result.axes.length >= 2 &&
    result.axes.length <= 6 &&
    result.axes.every(isAxisScore) &&
    isTypeResult(result.type) &&
    typeof result.completedAt === 'string' &&
    isValidISODate(result.completedAt)
  );
};

/**
 * AxisScore型ガード
 */
export const isAxisScore = (obj: unknown): obj is AxisScore => {
  if (!obj || typeof obj !== 'object') return false;
  
  const axis = obj as AxisScore;
  
  return (
    typeof axis.id === 'string' &&
    AXIS_ID_PATTERN.test(axis.id) &&
    typeof axis.name === 'string' &&
    axis.name.length >= 1 &&
    axis.name.length <= 20 &&
    typeof axis.description === 'string' &&
    axis.description.length >= 1 &&
    axis.description.length <= 100 &&
    typeof axis.direction === 'string' &&
    DIRECTION_PATTERN.test(axis.direction) &&
    typeof axis.score === 'number' &&
    axis.score >= 0 &&
    axis.score <= 100 &&
    typeof axis.rawScore === 'number' &&
    axis.rawScore >= -5.0 &&
    axis.rawScore <= 5.0
  );
};

/**
 * TypeResult型ガード
 */
export const isTypeResult = (obj: unknown): obj is TypeResult => {
  if (!obj || typeof obj !== 'object') return false;
  
  const type = obj as TypeResult;
  
  return (
    typeof type.name === 'string' &&
    type.name.length >= 1 &&
    type.name.length <= 14 &&
    TYPE_NAME_PATTERN.test(type.name) &&
    typeof type.description === 'string' &&
    type.description.length >= 1 &&
    type.description.length <= 50 &&
    Array.isArray(type.dominantAxes) &&
    type.dominantAxes.length === 2 &&
    type.dominantAxes.every(id => typeof id === 'string' && AXIS_ID_PATTERN.test(id)) &&
    isPolarityPattern(type.polarity)
  );
};

/**
 * PolarityPattern型ガード
 */
export const isPolarityPattern = (value: unknown): value is PolarityPattern => {
  return typeof value === 'string' && [
    'Hi-Hi', 'Hi-Lo', 'Lo-Hi', 'Lo-Lo',
    'Hi-Mid', 'Lo-Mid', 'Mid-Hi', 'Mid-Lo', 'Mid-Mid'
  ].includes(value);
};

/**
 * ErrorResponse型ガード
 */
export const isErrorResponse = (obj: unknown): obj is ErrorResponse => {
  if (!obj || typeof obj !== 'object') return false;
  
  const error = obj as ErrorResponse;
  
  return (
    typeof error.error === 'object' &&
    error.error !== null &&
    typeof error.error.code === 'string' &&
    typeof error.error.message === 'string' &&
    (error.sessionId === undefined || typeof error.sessionId === 'string')
  );
};

// ===== Utility Functions =====

/**
 * ISO 8601日時文字列検証
 */
export const isValidISODate = (dateString: string): boolean => {
  try {
    const date = new Date(dateString);
    return date.toISOString() === dateString;
  } catch {
    return false;
  }
};

/**
 * スコア正規化関数
 * rawScore（-5.0〜5.0）をscore（0〜100）に変換
 */
export const normalizeScore = (rawScore: number): number => {
  const MIN_RAW = -5.0;
  const MAX_RAW = 5.0;
  
  const normalized = ((rawScore - MIN_RAW) / (MAX_RAW - MIN_RAW)) * 100;
  return Math.max(0, Math.min(100, Math.round(normalized * 10) / 10));
};

/**
 * 極性判定関数
 * スコア値から極性（Hi/Mid/Lo）を判定
 */
export const determinePolarity = (score: number): 'Hi' | 'Mid' | 'Lo' => {
  if (score >= 60) return 'Hi';
  if (score <= 40) return 'Lo';
  return 'Mid';
};

/**
 * 極性パターン生成関数
 * 2つの軸スコアから極性パターンを生成
 */
export const createPolarityPattern = (scoreA: number, scoreB: number): PolarityPattern => {
  const polarityA = determinePolarity(scoreA);
  const polarityB = determinePolarity(scoreB);
  return `${polarityA}-${polarityB}` as PolarityPattern;
};

// ===== Mock Data =====

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

/**
 * データバリデーションユーティリティ
 *
 * API レスポンスの型ガードと検証ロジック
 */

import type { ResultData, AxisScore, TypeResult, ErrorResponse } from '@/types/result';
import {
  isResultData,
  isAxisScore,
  isTypeResult,
  isErrorResponse,
} from '@/types/result';

/**
 * ResultData の完全な検証（型ガード + ビジネスルール）
 */
export function validateResultData(data: unknown): { valid: true; data: ResultData } | { valid: false; error: string } {
  // 型ガードによる基本検証
  if (!isResultData(data)) {
    return {
      valid: false,
      error: 'Invalid ResultData structure'
    };
  }

  // ビジネスルール検証
  const errors: string[] = [];

  // 軸数の検証（2-6軸）
  if (data.axes.length < 2 || data.axes.length > 6) {
    errors.push(`軸数が範囲外です: ${data.axes.length} (2-6軸が必要)`);
  }

  // 各軸のスコア範囲検証
  data.axes.forEach((axis, index) => {
    if (axis.score < 0 || axis.score > 100) {
      errors.push(`軸${index + 1}のスコアが範囲外です: ${axis.score} (0-100が必要)`);
    }
    if (axis.rawScore < -5.0 || axis.rawScore > 5.0) {
      errors.push(`軸${index + 1}の生スコアが範囲外です: ${axis.rawScore} (-5.0〜5.0が必要)`);
    }
  });

  // タイプの主軸検証
  const axisIds = new Set(
    data.axes
      .map(axis => axis.id ?? axis.axisId)
      .filter((axisId): axisId is string => typeof axisId === 'string' && axisId.length > 0)
  );
  data.type.dominantAxes.forEach(axisId => {
    if (typeof axisId !== 'string' || axisId.length === 0 || !axisIds.has(axisId)) {
      errors.push(`主軸 ${axisId} が軸データに存在しません`);
    }
  });

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; ')
    };
  }

  return {
    valid: true,
    data
  };
}

/**
 * AxisScore の検証
 */
export function validateAxisScore(data: unknown): { valid: true; data: AxisScore } | { valid: false; error: string } {
  if (!isAxisScore(data)) {
    return {
      valid: false,
      error: 'Invalid AxisScore structure'
    };
  }

  return {
    valid: true,
    data
  };
}

/**
 * TypeResult の検証
 */
export function validateTypeResult(data: unknown): { valid: true; data: TypeResult } | { valid: false; error: string } {
  if (!isTypeResult(data)) {
    return {
      valid: false,
      error: 'Invalid TypeResult structure'
    };
  }

  return {
    valid: true,
    data
  };
}

/**
 * ErrorResponse の検証
 */
export function validateErrorResponse(data: unknown): { valid: true; data: ErrorResponse } | { valid: false; error: string } {
  if (!isErrorResponse(data)) {
    return {
      valid: false,
      error: 'Invalid ErrorResponse structure'
    };
  }

  return {
    valid: true,
    data
  };
}

/**
 * セッションID の検証（UUID v4形式）
 */
export function validateSessionId(sessionId: string): boolean {
  const uuidV4Pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidV4Pattern.test(sessionId);
}

/**
 * ISO 8601 日時文字列の検証
 */
export function validateISODate(dateString: string): boolean {
  try {
    const date = new Date(dateString);
    return date.toISOString() === dateString;
  } catch {
    return false;
  }
}

/**
 * スコア値の正規化範囲検証（0-100）
 */
export function validateNormalizedScore(score: number): boolean {
  return score >= 0 && score <= 100;
}

/**
 * 生スコア値の範囲検証（-5.0〜5.0）
 */
export function validateRawScore(rawScore: number): boolean {
  return rawScore >= -5.0 && rawScore <= 5.0;
}

/**
 * 軸数の範囲検証（2-6軸）
 */
export function validateAxesCount(count: number): boolean {
  return count >= 2 && count <= 6;
}

/**
 * レスポンスデータの安全な解析
 */
export async function safeParseResponse<T>(
  response: Response,
  validator: (data: unknown) => { valid: true; data: T } | { valid: false; error: string }
): Promise<{ success: true; data: T } | { success: false; error: string }> {
  try {
    const data = await response.json();
    const validation = validator(data);

    if (!validation.valid) {
      return {
        success: false,
        error: validation.error
      };
    }

    return {
      success: true,
      data: validation.data
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'JSON parse error'
    };
  }
}

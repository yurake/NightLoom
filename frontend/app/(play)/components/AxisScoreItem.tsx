/**
 * AxisScoreItem コンポーネント
 * 
 * 個別軸スコアを表示するアイテムコンポーネント
 * - スコアバーアニメーション（1秒、ease-out）
 * - 軸名・方向性・スコア数値表示
 * - アクセシビリティ対応
 * - prefers-reduced-motion対応
 */

import React, { useState, useEffect } from 'react';
import type { AxisScore } from '@/types/result';

export type { AxisScore };

export interface AxisScoreItemProps {
  /**
   * 軸スコアデータ
   * @description 個別の評価軸のスコア情報（ID、名前、説明、方向性、スコア値）
   */
  axisScore: AxisScore;
}

/**
 * AxisScoreItem コンポーネント
 *
 * @description 個別の軸スコアを視覚化するアイテムコンポーネント
 *
 * @features
 * - プログレスバーによるスコア可視化（0-100%）
 * - 1秒間のスムーズアニメーション（100ms遅延、ease-out）
 * - 軸名・方向性・スコア数値の表示
 * - レスポンシブデザイン（360px-1920px対応）
 * - prefers-reduced-motion 対応（モーション無効化）
 *
 * @accessibility
 * - ARIA progressbar 属性による適切なスクリーンリーダー対応
 * - aria-label, aria-valuenow, aria-valuemin, aria-valuemax
 * - live region による動的更新の通知
 * - 詳細なスコア情報の提供（生スコア、正規化スコア）
 *
 * @animation
 * - CSS transition: 1s ease-out
 * - 100ms 遅延後のアニメーション開始
 * - prefers-reduced-motion: reduce 時の即座表示
 *
 * @example
 * ```tsx
 * const axisData = {
 *   id: "axis_1",
 *   name: "論理性",
 *   description: "論理的思考の傾向",
 *   direction: "論理的 ← → 感情的",
 *   score: 75.5,
 *   rawScore: 2.1
 * };
 *
 * <AxisScoreItem axisScore={axisData} />
 * ```
 *
 * @param props - AxisScoreItemProps
 * @returns JSX要素
 */
export const AxisScoreItem: React.FC<AxisScoreItemProps> = ({ axisScore }) => {
  const [animatedWidth, setAnimatedWidth] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const axisId = axisScore.id ?? axisScore.axisId ?? 'axis';
  const axisName = axisScore.name ?? axisId;
  const axisDirection = axisScore.direction ?? '';
  const axisDescription = axisScore.description ?? '';
  const rawScore = axisScore.rawScore ?? 0;
  const normalizedScore = axisScore.score ?? 0;

  useEffect(() => {
    // prefers-reduced-motion チェック（テスト環境対応）
    const prefersReducedMotion = typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      // モーション無効化の場合、即座に最終値を設定
      setAnimatedWidth(normalizedScore);
      return;
    }

    // 100ms遅延後にアニメーション開始
    const timer = setTimeout(() => {
      setIsAnimating(true);
      setAnimatedWidth(normalizedScore);
    }, 100);

    return () => clearTimeout(timer);
  }, [normalizedScore]);

  return (
    <div
      className="p-3 xs:p-4 sm:p-5 rounded-lg xs:rounded-xl bg-white shadow-sm border border-gray-200 group"
      role="group"
      aria-labelledby={`axis-name-${axisId}`}
      aria-describedby={`axis-description-${axisId} axis-direction-${axisId}`}
      data-testid={`axis-${axisId}`}
    >
      {/* 軸名と方向性 */}
      <div className="mb-3 xs:mb-4">
        <h3
          id={`axis-name-${axisId}`}
          className="text-sm xs:text-base sm:text-lg font-semibold text-gray-900 mb-1 leading-tight"
        >
          {axisName}
        </h3>
        <p
          id={`axis-direction-${axisId}`}
          className="text-xs xs:text-sm text-gray-600 leading-snug"
        >
          {axisDirection}
        </p>
      </div>

      {/* プログレスバーとスコア */}
      <div className="flex items-center gap-2 xs:gap-3 sm:gap-4">
        <div
          className="flex-1 h-2 xs:h-3 sm:h-4 bg-gray-200 rounded-full overflow-hidden"
          role="progressbar"
          aria-label={`${axisName}のスコア: ${normalizedScore.toFixed(1)}点（100点満点）`}
          aria-valuenow={Math.round(normalizedScore)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuetext={`${normalizedScore.toFixed(1)}点`}
        >
          <div
            data-testid="progress-fill"
            className={`h-full bg-gradient-to-r from-blue-500 to-purple-600 motion-safe:transition-all motion-safe:duration-1000 motion-safe:ease-out ${
              isAnimating ? '' : 'transition-none'
            }`}
            style={{
              width: `${animatedWidth}%`
            }}
            aria-hidden="true"
          />
        </div>
        <span
          className="text-sm xs:text-base sm:text-lg font-medium text-gray-900 min-w-[2.5rem] xs:min-w-[3rem] text-right tabular-nums"
          aria-label={`スコア値: ${normalizedScore.toFixed(1)}点`}
        >
          {normalizedScore.toFixed(1)}
        </span>
      </div>

      {/* 軸説明（モバイルで常時表示、デスクトップでホバー表示） */}
      <div className="mt-2 xs:mt-3">
        <p
          id={`axis-description-${axisId}`}
          className="text-xs xs:text-sm text-gray-500 sm:opacity-0 sm:group-hover:opacity-100 motion-safe:transition-opacity motion-safe:duration-200 sm:md:opacity-100 leading-relaxed"
        >
          {axisDescription}
        </p>
        
        {/* スクリーンリーダー専用の詳細情報 */}
        <div className="sr-only">
          <p>
            生スコア: {rawScore.toFixed(2)}（理論範囲: -5.0から5.0）
          </p>
          <p>
            正規化スコア: {normalizedScore.toFixed(1)}（0から100）
          </p>
        </div>
      </div>

      {/* スコア変更の通知（動的更新時） */}
      <div
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {isAnimating && `${axisName}のスコアが更新されました: ${normalizedScore.toFixed(1)}点`}
      </div>
    </div>
  );
};

export default AxisScoreItem;

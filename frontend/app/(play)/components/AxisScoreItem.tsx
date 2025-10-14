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
  /** 軸スコアデータ */
  axisScore: AxisScore;
}

/**
 * AxisScoreItem コンポーネント
 */
export const AxisScoreItem: React.FC<AxisScoreItemProps> = ({ axisScore }) => {
  const [animatedWidth, setAnimatedWidth] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    // prefers-reduced-motion チェック（テスト環境対応）
    const prefersReducedMotion = typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      // モーション無効化の場合、即座に最終値を設定
      setAnimatedWidth(axisScore.score);
      return;
    }

    // 100ms遅延後にアニメーション開始
    const timer = setTimeout(() => {
      setIsAnimating(true);
      setAnimatedWidth(axisScore.score);
    }, 100);

    return () => clearTimeout(timer);
  }, [axisScore.score]);

  return (
    <div className="p-4 rounded-lg bg-white shadow-sm border border-gray-200">
      {/* 軸名と方向性 */}
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">
          {axisScore.name}
        </h3>
        <p className="text-xs text-gray-600">
          {axisScore.direction}
        </p>
      </div>

      {/* プログレスバーとスコア */}
      <div className="flex items-center gap-3">
        <div
          className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden"
          role="progressbar"
          aria-label={`${axisScore.name}の進捗: ${axisScore.score.toFixed(1)}パーセント`}
          aria-valuenow={axisScore.score}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            data-testid="progress-fill"
            className={`h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-1000 ease-out ${
              isAnimating ? '' : 'transition-none'
            }`}
            style={{ 
              width: `${animatedWidth}%`
            }}
          />
        </div>
        <span className="text-sm font-medium text-gray-900 min-w-[3rem] text-right">
          {axisScore.score.toFixed(1)}
        </span>
      </div>

      {/* 軸説明（ホバー時表示） */}
      <div className="mt-2">
        <p className="text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {axisScore.description}
        </p>
      </div>
    </div>
  );
};

export default AxisScoreItem;

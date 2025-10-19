/**
 * AxesScores コンポーネント
 * 
 * 軸スコア一覧を表示するコンテナコンポーネント
 * - 2〜6軸の動的レンダリング
 * - レスポンシブグリッドレイアウト
 * - AxisScoreItemコンポーネントの配列レンダリング
 */

import React from 'react';
import { AxisScoreItem, type AxisScore } from './AxisScoreItem';

export interface AxesScoresProps {
  /**
   * 軸スコア配列データ
   * @description 複数の評価軸スコアの配列（2-6軸対応）
   */
  axesScores: AxisScore[];
}

/**
 * AxesScores コンポーネント
 *
 * @description 複数の軸スコアを一覧表示するコンテナコンポーネント
 *
 * @features
 * - 2-6軸の動的レンダリング対応
 * - レスポンシブグリッドレイアウト（軸数に応じて自動調整）
 * - AxisScoreItemコンポーネントの統合表示
 * - 空状態の適切な表示
 * - アクセシビリティ対応のセクション構造
 *
 * @layout
 * - モバイル（360px-）: 1列表示
 * - タブレット（640px-）: 2列表示
 * - デスクトップ（1024px-）: 軸数に応じて2-3列表示
 *
 * @accessibility
 * - region role による意味的なセクション定義
 * - 軸数の明示的な表示とaria-label
 * - 空状態の視覚的・音声的フィードバック
 *
 * @example
 * ```tsx
 * const axesData = [
 *   {
 *     id: "axis_1",
 *     name: "論理性",
 *     score: 75.5,
 *     // ... other properties
 *   },
 *   {
 *     id: "axis_2",
 *     name: "社交性",
 *     score: 42.3,
 *     // ... other properties
 *   }
 * ];
 *
 * <AxesScores axesScores={axesData} />
 * ```
 *
 * @param props - AxesScoresProps
 * @returns JSX要素
 */
export const AxesScores: React.FC<AxesScoresProps> = ({ axesScores }) => {
  // モバイル対応のグリッドレイアウトの決定
  const getGridClasses = (axesCount: number) => {
    if (axesCount <= 2) {
      return 'grid-cols-1 xs:grid-cols-1 sm:grid-cols-2';
    } else if (axesCount <= 4) {
      return 'grid-cols-1 xs:grid-cols-1 sm:grid-cols-2 lg:grid-cols-2';
    } else {
      return 'grid-cols-1 xs:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
    }
  };

  return (
    <section
      className="w-full px-2 xs:px-0"
      role="region"
      aria-label={`軸スコア一覧 (${axesScores.length}軸)`}
      data-testid="axes-section"
    >
      {/* セクションタイトル */}
      <h2
        className="text-base xs:text-lg sm:text-xl font-semibold text-gray-900 mb-3 xs:mb-4 sm:mb-6 text-center xs:text-left"
        data-testid="axes-title"
      >
        軸スコア ({axesScores.length}軸)
      </h2>

      {/* 軸スコア一覧グリッド */}
      <div className={`grid gap-3 xs:gap-4 sm:gap-6 ${getGridClasses(axesScores.length)}`}>
        {axesScores.map((axisScore) => (
          <AxisScoreItem
            key={axisScore.id}
            axisScore={axisScore}
          />
        ))}
      </div>

      {/* 空状態の表示 */}
      {axesScores.length === 0 && (
        <div className="text-center text-gray-500 py-6 xs:py-8 sm:py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-sm xs:text-base">軸スコアデータがありません</p>
        </div>
      )}
    </section>
  );
};

export default AxesScores;

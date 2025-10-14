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
  /** 軸スコア配列データ */
  axesScores: AxisScore[];
}

/**
 * AxesScores コンポーネント
 */
export const AxesScores: React.FC<AxesScoresProps> = ({ axesScores }) => {
  // グリッドレイアウトの決定
  const getGridClasses = (axesCount: number) => {
    if (axesCount <= 2) {
      return 'grid-cols-1';
    } else if (axesCount <= 4) {
      return 'grid-cols-1 md:grid-cols-2';
    } else {
      return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    }
  };

  return (
    <section
      className="w-full"
      role="region"
      aria-label={`軸スコア一覧 (${axesScores.length}軸)`}
    >
      {/* セクションタイトル */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        軸スコア ({axesScores.length}軸)
      </h2>

      {/* 軸スコア一覧グリッド */}
      <div className={`grid gap-4 ${getGridClasses(axesScores.length)}`}>
        {axesScores.map((axisScore) => (
          <AxisScoreItem
            key={axisScore.id}
            axisScore={axisScore}
          />
        ))}
      </div>

      {/* 空状態の表示 */}
      {axesScores.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <p>軸スコアデータがありません</p>
        </div>
      )}
    </section>
  );
};

export default AxesScores;

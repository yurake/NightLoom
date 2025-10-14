/**
 * TypeCard コンポーネント
 * 
 * タイプ分類結果を表示するカードコンポーネント
 * - タイプ名・説明・極性バッジ・主軸情報を表示
 * - グラデーション背景による視覚的強調
 * - レスポンシブデザイン対応
 */

import React from 'react';
import type { TypeResult } from '@/types/result';

export type { TypeResult };

export interface TypeCardProps {
  /** タイプ分類結果データ */
  typeResult: TypeResult;
}

/**
 * TypeCard コンポーネント
 */
export const TypeCard: React.FC<TypeCardProps> = ({ typeResult }) => {
  return (
    <article
      className="p-4 md:p-6 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg"
      role="article"
      aria-label={`診断結果: ${typeResult.name}タイプ`}
    >
      {/* タイプ名 */}
      <h2 className="text-xl md:text-2xl font-bold mb-2 text-center">
        {typeResult.name}
      </h2>

      {/* 極性バッジ */}
      <div className="flex justify-center mb-4">
        <span className="px-3 py-1 bg-white bg-opacity-20 rounded-full text-sm font-medium">
          {typeResult.polarity}
        </span>
      </div>

      {/* タイプ説明 */}
      <p className="text-sm md:text-base leading-relaxed text-center mb-4">
        {typeResult.description}
      </p>

      {/* 主軸情報 */}
      <div className="text-center">
        <p className="text-xs md:text-sm opacity-90">
          主軸: {typeResult.dominantAxes.length}軸
        </p>
      </div>
    </article>
  );
};

export default TypeCard;

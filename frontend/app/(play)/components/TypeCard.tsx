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
      className="p-4 xs:p-5 sm:p-6 rounded-lg xs:rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg mx-2 xs:mx-0"
      role="article"
      aria-labelledby="type-name"
      aria-describedby="type-description type-details"
    >
      {/* タイプ名 */}
      <h2
        id="type-name"
        className="text-lg xs:text-xl sm:text-2xl md:text-3xl font-bold mb-3 xs:mb-4 text-center leading-tight"
      >
        {typeResult.name}
      </h2>

      {/* 極性バッジ */}
      <div className="flex justify-center mb-4 xs:mb-5">
        <span
          className="px-3 xs:px-4 py-1 xs:py-1.5 bg-white bg-opacity-20 rounded-full text-xs xs:text-sm sm:text-base font-medium min-h-[32px] flex items-center"
          role="status"
          aria-label={`極性パターン: ${typeResult.polarity}`}
        >
          {typeResult.polarity}
        </span>
      </div>

      {/* タイプ説明 */}
      <p
        id="type-description"
        className="text-sm xs:text-base sm:text-lg leading-relaxed text-center mb-4 xs:mb-5 px-2 xs:px-0"
      >
        {typeResult.description}
      </p>

      {/* 主軸情報 */}
      <div
        id="type-details"
        className="text-center"
      >
        <p className="text-xs xs:text-sm sm:text-base opacity-90">
          <span className="sr-only">このタイプの</span>
          主軸: <span aria-label={`${typeResult.dominantAxes.length}つの軸`}>{typeResult.dominantAxes.length}軸</span>
        </p>
        
        {/* 主軸リスト（スクリーンリーダー用） */}
        <div className="sr-only">
          <h3>主要な評価軸:</h3>
          <ul>
            {typeResult.dominantAxes.map((axisId, index) => (
              <li key={axisId}>
                軸{index + 1}: {axisId}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
};

export default TypeCard;

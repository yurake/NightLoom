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
  /**
   * タイプ分類結果データ
   * @description 診断結果から得られるパーソナリティタイプの情報
   */
  typeResult: TypeResult;
}

/**
 * TypeCard コンポーネント
 *
 * @description 診断結果のパーソナリティタイプを表示するカードコンポーネント
 *
 * @features
 * - タイプ名の表示（レスポンシブフォントサイズ対応）
 * - 極性パターンバッジの表示
 * - タイプ説明の表示（改行・長文対応）
 * - 主軸情報の表示（アクセシビリティ対応）
 * - グラデーション背景による視覚的強調
 * - 360px-1920px対応のレスポンシブデザイン
 *
 * @accessibility
 * - ARIA labels と role 属性による構造化
 * - スクリーンリーダー向けの詳細情報
 * - キーボードナビゲーション対応
 *
 * @example
 * ```tsx
 * const typeData = {
 *   name: "探求者タイプ",
 *   description: "好奇心旺盛で新しいことに挑戦する...",
 *   dominantAxes: ["axis_1", "axis_3"],
 *   polarity: "High-Mid"
 * };
 *
 * <TypeCard typeResult={typeData} />
 * ```
 *
 * @param props - TypeCardProps
 * @returns JSX要素
 */
export const TypeCard: React.FC<TypeCardProps> = ({ typeResult }) => {
  const typeName = typeResult.name ?? '診断タイプ';
  const normalizedTestId = `type-${typeName.toLowerCase().replace(/\s+/g, '-')}`;
  const dominantAxes = Array.isArray(typeResult.dominantAxes) ? typeResult.dominantAxes : [];
  const polarity = typeResult.polarity ?? 'Mid-Mid';
  const description = typeResult.description ?? 'タイプ情報を取得できませんでした。';

  return (
    <section data-testid="type-profiles-section">
      <h2 data-testid="types-title" className="sr-only" aria-hidden="true">パーソナリティタイプ</h2>
      <article
        className="p-4 xs:p-5 sm:p-6 rounded-lg xs:rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg mx-2 xs:mx-0"
        role="article"
        aria-labelledby="type-name"
        aria-describedby="type-description type-details"
        data-testid={normalizedTestId}
      >
      {/* タイプ名 */}
      <h2
        id="type-name"
        className="text-lg xs:text-xl sm:text-2xl md:text-3xl font-bold mb-3 xs:mb-4 text-center leading-tight"
      >
        {typeName}
      </h2>

      {/* 極性バッジ */}
      <div className="flex justify-center mb-4 xs:mb-5">
        <span
          className="px-3 xs:px-4 py-1 xs:py-1.5 bg-white bg-opacity-20 rounded-full text-xs xs:text-sm sm:text-base font-medium min-h-[32px] flex items-center"
          role="status"
          aria-label={`極性パターン: ${polarity}`}
        >
          {polarity}
        </span>
      </div>

      {/* タイプ説明 */}
      <p
        id="type-description"
        className="text-sm xs:text-base sm:text-lg leading-relaxed text-center mb-4 xs:mb-5 px-2 xs:px-0"
      >
        {description}
      </p>

      {/* 主軸情報 */}
      <div
        id="type-details"
        className="text-center"
      >
        <p className="text-xs xs:text-sm sm:text-base opacity-90">
          <span className="sr-only">このタイプの</span>
          主軸: <span aria-label={`${dominantAxes.length}つの軸`}>{dominantAxes.length}軸</span>
        </p>
        
        {/* 主軸リスト（スクリーンリーダー用） */}
        <div className="sr-only">
          <h3>主要な評価軸:</h3>
          <ul>
            {dominantAxes.map((axisId, index) => (
              <li key={axisId}>
                軸{index + 1}: {axisId}
              </li>
            ))}
          </ul>
        </div>
      </div>
      </article>
    </section>
  );
};

export default TypeCard;

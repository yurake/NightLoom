/**
 * 結果画面ページ
 * 
 * Next.js 14 App Router対応
 * - ResultScreenコンポーネントを配置
 * - sessionId取得とAPIクライアント統合
 * - SEO・メタデータ設定
 */

'use client';

import React from 'react';
import { useSearchParams } from 'next/navigation';
import { ResultScreen } from '../components/ResultScreen';
import { defaultApiClient } from '../../services/session-api';

/**
 * 結果画面ページコンポーネント
 */
export default function ResultPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');

  // sessionIdが存在しない場合のエラーハンドリング
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            無効なアクセスです
          </h1>
          <p className="text-gray-600 mb-6">
            セッションIDが指定されていません。
          </p>
          <a
            href="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            診断を開始する
          </a>
        </div>
      </div>
    );
  }

  return (
    <ResultScreen 
      sessionId={sessionId} 
      apiClient={defaultApiClient} 
    />
  );
}

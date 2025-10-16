/**
 * ResultScreen コンポーネント
 * 
 * 結果画面のメインコンテナコンポーネント
 * - API呼び出しと状態管理
 * - TypeCard + AxesScores の統合表示
 * - ローディング・エラー状態の管理
 */

import React, { useState, useEffect } from 'react';
import { TypeCard, type TypeResult } from './TypeCard';
import { AxesScores, type AxesScoresProps } from './AxesScores';
import type { ResultData, AxisScore } from '@/types/result';

// APIクライアントインターフェース
interface ApiClient {
  getResult(sessionId: string): Promise<ResultData>;
}

export interface ResultScreenProps {
  /** セッションID */
  sessionId: string;
  /** APIクライアント（依存性注入） */
  apiClient: ApiClient;
}

/**
 * LoadingIndicator コンポーネント
 */
const LoadingIndicator: React.FC = () => (
  <div
    className="flex flex-col items-center justify-center py-12"
    data-testid="loading-indicator"
  >
    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full motion-safe:animate-spin mb-4"></div>
    <p className="text-gray-600">読み込み中...</p>
    {/* Alternative static indicator for reduced motion users */}
    <div className="sr-only" aria-live="polite">
      診断結果を読み込んでいます
    </div>
  </div>
);

/**
 * ErrorMessage コンポーネント
 */
interface ErrorMessageProps {
  error: any;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ error }) => {
  const getErrorMessage = (error: any): string => {
    if (error?.code === 'SESSION_NOT_FOUND') {
      return 'セッションが見つかりません';
    }
    if (error?.code === 'SESSION_NOT_COMPLETED') {
      return '診断が完了していません';
    }
    if (error?.code === 'NETWORK_ERROR') {
      return 'ネットワークエラーが発生しました';
    }
    if (error?.message) {
      // 一般的なエラーメッセージの場合、より親しみやすいメッセージに変換
      if (error.message === 'API Error') {
        return 'エラーが発生しました';
      }
      return error.message;
    }
    return 'エラーが発生しました';
  };

  return (
    <div 
      className="flex flex-col items-center justify-center py-12 text-center"
      data-testid="error-message"
    >
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {getErrorMessage(error)}
      </h3>
      <p className="text-gray-600">
        しばらく待ってから再度お試しください
      </p>
    </div>
  );
};

/**
 * ResultScreen コンポーネント
 */
export const ResultScreen: React.FC<ResultScreenProps> = ({ sessionId, apiClient }) => {
  const [result, setResult] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const resultData = await apiClient.getResult(sessionId);
        setResult(resultData);
      } catch (err) {
        setError(err);
        console.error('結果取得エラー:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [sessionId, apiClient]);

  return (
    <main
      className="min-h-screen min-h-dvh bg-gray-50 py-4 xs:py-6 sm:py-8 pb-safe"
      role="main"
      aria-label="診断結果画面"
    >
      <div className="max-w-4xl mx-auto container-mobile">
        {/* Screen reader announcement for result completion */}
        <div
          className="sr-only"
          role="status"
          aria-live="polite"
          data-testid="result-announcement"
        >
          {result && !isLoading && !error && "診断が完了しました。結果をご確認ください。"}
        </div>

        {isLoading && <LoadingIndicator />}
        
        {error && <ErrorMessage error={error} />}
        
        {result && !isLoading && !error && (
          <div className="spacing-mobile">
            {/* Page heading */}
            <header className="text-center mb-6 xs:mb-8">
              <h1 className="text-xl xs:text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                あなたの診断結果
              </h1>
              <p className="text-mobile-body text-gray-600">
                パーソナリティ分析が完了しました
              </p>
            </header>

            {/* タイプカード */}
            <section
              aria-labelledby="type-section-heading"
              role="region"
            >
              <h2
                id="type-section-heading"
                className="sr-only"
              >
                パーソナリティタイプ
              </h2>
              <TypeCard typeResult={result.type} />
            </section>
            
            {/* 軸スコア一覧 */}
            <section
              aria-labelledby="scores-section-heading"
              role="region"
            >
              <h2
                id="scores-section-heading"
                className="sr-only"
              >
                詳細スコア
              </h2>
              <AxesScores axesScores={result.axes} />
            </section>
            
            {/* 診断情報 */}
            <section
              className="text-center text-xs xs:text-sm text-gray-500 px-2"
              aria-labelledby="session-info-heading"
              role="complementary"
            >
              <h2
                id="session-info-heading"
                className="sr-only"
              >
                診断セッション情報
              </h2>
              <dl className="space-y-1">
                <div>
                  <dt className="sr-only">診断キーワード</dt>
                  <dd className="break-words">診断キーワード: {result.keyword}</dd>
                </div>
                <div>
                  <dt className="sr-only">完了日時</dt>
                  <dd className="break-words">完了日時: {new Date(result.completedAt).toLocaleString('ja-JP')}</dd>
                </div>
              </dl>
            </section>

            {/* 再診断ボタン */}
            <section className="text-center mt-8 xs:mt-10 sm:mt-12 pb-4">
              <button
                onClick={() => window.location.href = '/'}
                className="w-full xs:w-auto bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium py-3 px-6 xs:px-8 rounded-lg motion-safe:transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 min-h-[44px]"
                aria-describedby="restart-help"
              >
                もう一度診断する
              </button>
              <div
                id="restart-help"
                className="sr-only"
              >
                新しい診断セッションを開始します
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
};

export default ResultScreen;

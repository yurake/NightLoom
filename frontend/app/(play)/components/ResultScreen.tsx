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
    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
    <p className="text-gray-600">読み込み中...</p>
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
      className="min-h-screen bg-gray-50 py-8"
      role="main"
      aria-label="診断結果画面"
    >
      <div className="max-w-4xl mx-auto px-4">
        {isLoading && <LoadingIndicator />}
        
        {error && <ErrorMessage error={error} />}
        
        {result && !isLoading && !error && (
          <div className="space-y-8">
            {/* タイプカード */}
            <TypeCard typeResult={result.type} />
            
            {/* 軸スコア一覧 */}
            <AxesScores axesScores={result.axes} />
            
            {/* 診断情報 */}
            <div className="text-center text-sm text-gray-500">
              <p>診断キーワード: {result.keyword}</p>
              <p>完了日時: {new Date(result.completedAt).toLocaleString('ja-JP')}</p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};

export default ResultScreen;

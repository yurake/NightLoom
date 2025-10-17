'use client';

/**
 * ResultScreen コンポーネント
 *
 * 診断結果の表示・エラー処理を司るメインコンテナ。
 * API から取得した生データを UI コンポーネント向けに整形して渡す。
 */

import React, { useEffect, useMemo, useState } from 'react';
import { TypeCard, type TypeResult } from './TypeCard';
import { AxesScores, type AxesScoresProps } from './AxesScores';
import type { ResultData } from '@/types/result';

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

const LoadingIndicator: React.FC = () => (
  <div
    className="flex flex-col items-center justify-center py-12"
    data-testid="loading-indicator"
  >
    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full motion-safe:animate-spin mb-4" />
    <p className="text-gray-600">読み込み中...</p>
    <div className="sr-only" aria-live="polite">
      診断結果を読み込んでいます
    </div>
  </div>
);

interface ErrorMessageProps {
  error: any;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ error }) => {
  const getErrorMessage = (): string => {
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
      if (error.message === 'API Error') {
        return 'エラーが発生しました';
      }
      return error.message;
    }
    return 'エラーが発生しました';
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center" data-testid="error-message">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
        <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 className="mb-2 text-lg font-semibold text-gray-900">{getErrorMessage()}</h3>
      <p className="text-gray-600">しばらく待ってから再度お試しください</p>
    </div>
  );
};

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
        console.error('結果取得エラー:', err);
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [sessionId, apiClient]);

  const typeCardData: TypeResult | null = useMemo(() => {
    if (!result?.type?.profiles?.length) {
      return null;
    }

    const profile = result.type.profiles[0];
    if (!profile?.name) {
      return null;
    }

    const dominantAxes = profile.dominantAxes ?? [];
    const safeDominantAxes: [string, string] = [
      dominantAxes[0] ?? 'axis_1',
      dominantAxes[1] ?? 'axis_2',
    ];

    const polarity = (profile.polarity ?? 'Mid-Mid') as TypeResult['polarity'];

    return {
      name: profile.name,
      description: profile.description ?? '診断タイプの説明を取得できませんでした。',
      dominantAxes: safeDominantAxes,
      polarity,
    };
  }, [result]);

  const axesScores: AxesScoresProps['axesScores'] = useMemo(() => {
    if (!result?.axes) {
      return [];
    }

    return result.axes.map((axis, index) => {
      const fallbackId = `axis_${index + 1}`;
      const rawId = (axis as any)?.axisId;

      return {
        id: axis.id ?? rawId ?? fallbackId,
        name: axis.name ?? axis.id ?? rawId ?? `軸${index + 1}`,
        description: axis.description ?? '',
        direction: axis.direction ?? '',
        score: axis.score ?? 0,
        rawScore: axis.rawScore ?? 0,
      };
    });
  }, [result]);

  return (
    <main
      className="min-h-screen min-h-dvh bg-gray-50 py-4 xs:py-6 sm:py-8 pb-safe"
      role="main"
      aria-label="診断結果画面"
    >
      <div className="container-mobile mx-auto max-w-4xl">
        <div className="sr-only" role="status" aria-live="polite" data-testid="result-announcement">
          {result && !isLoading && !error && '診断が完了しました。結果をご確認ください。'}
        </div>

        {isLoading && <LoadingIndicator />}
        {error && <ErrorMessage error={error} />}

        {result && !isLoading && !error && (
          <div className="spacing-mobile">
            <header className="mb-6 text-center xs:mb-8">
              <h1 className="mb-2 text-xl font-bold text-gray-900 xs:text-2xl sm:text-3xl">
                あなたの診断結果
              </h1>
              <p className="text-mobile-body text-gray-600">パーソナリティ分析が完了しました</p>
            </header>

            <section aria-labelledby="type-section-heading" role="region">
              <h2 id="type-section-heading" className="sr-only">
                パーソナリティタイプ
              </h2>
              {typeCardData ? (
                <TypeCard typeResult={typeCardData} />
              ) : (
                <div className="rounded-xl border border-gray-200 bg-white p-6 text-center text-gray-600">
                  タイプ情報を取得できませんでした。後でもう一度お試しください。
                </div>
              )}
            </section>

            <section aria-labelledby="scores-section-heading" role="region">
              <h2 id="scores-section-heading" className="sr-only">
                詳細スコア
              </h2>
              {axesScores.length > 0 ? (
                <AxesScores axesScores={axesScores} />
              ) : (
                <p className="text-center text-gray-600">スコア情報を取得できませんでした。</p>
              )}
            </section>

            <section
              className="px-2 text-center text-xs text-gray-500 xs:text-sm"
              aria-labelledby="session-info-heading"
              role="complementary"
            >
              <h2 id="session-info-heading" className="sr-only">
                診断セッション情報
              </h2>
              <dl className="space-y-1">
                <div>
                  <dt className="sr-only">診断キーワード</dt>
                  <dd className="break-words">診断キーワード: {result.keyword}</dd>
                </div>
                <div>
                  <dt className="sr-only">完了日時</dt>
                  <dd className="break-words">
                    完了日時: {new Date(result.completedAt).toLocaleString('ja-JP')}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="mt-8 pb-4 text-center xs:mt-10 sm:mt-12">
              <button
                onClick={() => window.location.href = '/'}
                className="w-full min-h-[44px] rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 active:bg-blue-800 xs:w-auto xs:px-8 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-describedby="restart-help"
              >
                もう一度診断する
              </button>
              <div id="restart-help" className="sr-only">
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

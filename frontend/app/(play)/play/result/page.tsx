/**
 * Result page for NightLoom diagnosis results
 * Displays final diagnosis with axes scores and type profiles
 */

'use client';

import React, { Suspense, useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '../../../state/SessionContext';
import { useTheme } from '../../../theme/ThemeProvider';
import { ResultScreen } from '../../components/ResultScreen';
import type { ResultData } from '@/types/result';

const LoadingFallback: React.FC = () => (
  <main
    className="result-page min-h-screen flex items-center justify-center p-8 bg-surface text-center text-white/80"
    data-testid="result-loading-suspense"
  >
    <div className="space-y-4">
      <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      <p className="text-sm text-white/70">結果画面を読み込み中...</p>
    </div>
  </main>
);

function ResultPageContent() {
  const [resultData, setResultData] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'session_expired' | 'service_unavailable' | 'general'>('general');

  const router = useRouter();
  const searchParams = useSearchParams();
  const { sessionState, clearSession } = useSession();
  useTheme();

  // Get session ID from URL params or session context
  const sessionId = searchParams?.get('sessionId') || sessionState?.id;

  const fetchResult = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/sessions/${sessionId}/result`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        switch (response.status) {
          case 404:
            setErrorType('session_expired');
            setError('セッションが見つかりません。新しい診断を開始してください。');
            break;
          case 400:
            if (errorData.error_code === 'SESSION_NOT_COMPLETED') {
              setErrorType('general');
              setError('診断が完了していません。4つのシーンを完了してから結果をご確認ください。');
            } else {
              setErrorType('general');
              setError('セッションの状態が無効です。新しい診断を開始してください。');
            }
            break;
          case 503:
            setErrorType('service_unavailable');
            setError('結果生成サービスが一時的に利用できません。');
            break;
          default:
            setErrorType('network');
            setError('結果の取得中にエラーが発生しました。');
        }
        return;
      }

      const data = await response.json();
      setResultData(data);
      
      // Update session context with result state
      if (sessionState) {
        sessionState.state = 'RESULT';
        sessionState.completedAt = data.completedAt;
      }

    } catch (err) {
      console.error('Error fetching result:', err);
      setErrorType('network');
      setError('ネットワークエラーが発生しました。接続を確認してください。');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, sessionState]);

  useEffect(() => {
    if (sessionId) {
      void fetchResult();
    } else {
      setError('セッションIDが見つかりません');
      setErrorType('session_expired');
      setIsLoading(false);
    }
  }, [sessionId, fetchResult]);

  const handleRestart = async () => {
    try {
      // Clean up current session if it exists
      if (sessionId) {
        await fetch(`/api/sessions/${sessionId}/cleanup`, {
          method: 'DELETE',
        });
      }
      
      // Clear session context
      clearSession();
      
      // Navigate to start page
      router.push('/');
      
    } catch (err) {
      console.error('Error during restart:', err);
      // Navigate anyway
      clearSession();
      router.push('/');
    }
  };

  const handleRetry = () => {
    void fetchResult();
  };

  // Loading state
  if (isLoading) {
    return (
      <main 
        className="result-page min-h-screen flex items-center justify-center p-8 bg-surface text-center text-white/80"
        data-testid="result-loading"
      >
        <div className="space-y-4">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <div>
            <p className="text-lg font-medium text-white">診断結果を生成中...</p>
            <p className="text-sm text-white/70">しばらくお待ちください</p>
          </div>
        </div>
      </main>
    );
  }

  // Error states
  if (error) {
    return (
      <main
        className="result-page min-h-screen flex items-center justify-center p-8 bg-surface"
        data-testid="error-container"
      >
        <div className="max-w-md space-y-5 text-center text-white/80">
          <h1 className="text-2xl font-semibold text-white">
            {errorType === 'session_expired'
              ? 'セッションが無効です'
              : 'エラーが発生しました'}
          </h1>
          <p data-testid="error-message">{error}</p>

          {errorType === 'session_expired' ? (
            <button
              onClick={handleRestart}
              className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent/90"
              data-testid="restart-button"
            >
              はじめに戻る
            </button>
          ) : (
            <div className="flex flex-col gap-3">
              {errorType === 'service_unavailable' || errorType === 'network' ? (
                <button
                  onClick={handleRetry}
                  className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent/90"
                  data-testid="retry-button"
                >
                  再試行
                </button>
              ) : null}
              <button
                onClick={handleRestart}
                className="w-full rounded-lg border border-white/30 px-4 py-2 font-medium text-white transition hover:border-white/60"
              >
                トップへ戻る
              </button>
            </div>
          )}
        </div>
      </main>
    );
  }

  if (!resultData) {
    return null;
  }

  return (
    <div className="result-page min-h-screen bg-surface" data-testid="result-container">
      <ResultScreen
        sessionId={resultData.sessionId}
        apiClient={{
          getResult: async () => resultData
        }}
      />
    </div>
  );
}

export default function ResultPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <ResultPageContent />
    </Suspense>
  );
}

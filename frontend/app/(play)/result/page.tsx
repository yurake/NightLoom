/**
 * Result page for NightLoom diagnosis results
 * Displays final diagnosis with axes scores and type profiles
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '@/app/state/SessionContext';
import { useTheme } from '@/app/theme/ThemeProvider';
import { ResultScreen } from '@/app/(play)/components/ResultScreen';
import { LoadingState, ErrorState, SessionExpiredState, ServiceUnavailableState } from '@/app/(play)/components/LoadingState';

interface AxisScore {
  axisId: string;
  score: number;
  rawScore: number;
}

interface TypeProfile {
  name: string;
  description: string;
  keywords: string[];
  dominantAxes: string[];
  polarity: string;
}

interface ResultData {
  sessionId: string;
  keyword: string;
  axes: AxisScore[];
  type: {
    dominantAxes: string[];
    profiles: TypeProfile[];
    fallbackUsed: boolean;
  };
  completedAt: string;
  fallbackFlags: string[];
}

export default function ResultPage() {
  const [resultData, setResultData] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'session_expired' | 'service_unavailable' | 'general'>('general');

  const router = useRouter();
  const searchParams = useSearchParams();
  const { sessionState, clearSession } = useSession();
  const { currentTheme, themeId } = useTheme();

  // Get session ID from URL params or session context
  const sessionId = searchParams?.get('sessionId') || sessionState?.sessionId;

  useEffect(() => {
    if (sessionId) {
      fetchResult();
    } else {
      setError('セッションIDが見つかりません');
      setErrorType('session_expired');
      setIsLoading(false);
    }
  }, [sessionId]);

  const fetchResult = async () => {
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
        sessionState.currentState = 'RESULT';
        sessionState.completedAt = data.completedAt;
      }

    } catch (err) {
      console.error('Error fetching result:', err);
      setErrorType('network');
      setError('ネットワークエラーが発生しました。接続を確認してください。');
    } finally {
      setIsLoading(false);
    }
  };

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
    fetchResult();
  };

  // Loading state
  if (isLoading) {
    return (
      <main 
        className="result-page min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: currentTheme.background }}
        data-testid="result-loading"
      >
        <LoadingState
          message="診断結果を生成中..."
          variant="spinner"
          size="lg"
          className="text-center"
        />
      </main>
    );
  }

  // Error states
  if (error) {
    return (
      <main
        className="result-page min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: currentTheme.background }}
        data-testid="error-container"
      >
        {errorType === 'session_expired' && (
          <SessionExpiredState
            onRestart={handleRestart}
            className="max-w-md mx-auto"
          />
        )}
        
        {errorType === 'service_unavailable' && (
          <ServiceUnavailableState
            onRetry={handleRetry}
            className="max-w-md mx-auto"
          />
        )}
        
        {(errorType === 'network' || errorType === 'general') && (
          <ErrorState
            title="エラーが発生しました"
            message={error}
            onRetry={errorType === 'network' ? handleRetry : undefined}
            className="max-w-md mx-auto"
          />
        )}
      </main>
    );
  }

  // No result data
  if (!resultData) {
    return (
      <main
        className="result-page min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: currentTheme.background }}
        data-testid="error-container"
      >
        <ErrorState
          title="結果が見つかりません"
          message="診断結果を取得できませんでした。新しい診断を開始してください。"
          onRetry={handleRestart}
          retryLabel="新しい診断を開始"
          className="max-w-md mx-auto"
        />
      </main>
    );
  }

  // Success - display results
  return (
    <main
      className="result-page min-h-screen"
      style={{ backgroundColor: currentTheme.background }}
      data-testid="result-container"
    >
      {/* Header */}
      <div className="result-header bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1
                className="text-xl font-bold"
                style={{ color: currentTheme.text.primary }}
                data-testid="result-title"
              >
                診断結果
              </h1>
              <p
                className="text-sm"
                style={{ color: currentTheme.text.secondary }}
                data-testid="keyword-display"
              >
                キーワード: {resultData.keyword}
              </p>
            </div>
            
            {/* Fallback indicator */}
            {resultData.fallbackFlags.length > 0 && (
              <div className="fallback-indicator">
                <span 
                  className="text-xs px-2 py-1 rounded-full"
                  style={{ 
                    backgroundColor: `${currentTheme.secondary}20`,
                    color: currentTheme.secondary 
                  }}
                  data-testid="fallback-indicator"
                >
                  基本的な結果
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Result Content */}
      <div className="result-content">
        <ResultScreen
          resultData={resultData}
          onRestart={handleRestart}
          className="max-w-4xl mx-auto p-4"
        />
      </div>

      {/* Footer Actions */}
      <div className="result-footer bg-white/80 backdrop-blur-sm border-t border-gray-200/50 mt-12">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center">
          <button
            onClick={handleRestart}
            className="restart-main-button px-8 py-3 rounded-lg font-semibold transition-all hover:shadow-lg"
            style={{
              backgroundColor: currentTheme.primary,
              color: 'white'
            }}
            data-testid="restart-button"
          >
            もう一度診断する
          </button>
          
          <p 
            className="text-sm mt-3"
            style={{ color: currentTheme.text.muted }}
          >
            診断結果はセッション終了後に自動的に削除されます
          </p>
        </div>
      </div>
    </main>
  );
}

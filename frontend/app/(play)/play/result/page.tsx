/**
 * Result page for NightLoom diagnosis results
 * Displays final diagnosis with axes scores and type profiles
 */

'use client';

import React, { Suspense, lazy } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '../../../state/SessionContext';
import { useTheme } from '../../../theme/ThemeProvider';

// Dynamic import for code splitting
const ResultScreen = lazy(() => import('../../components/ResultScreen'));

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
  const router = useRouter();
  const searchParams = useSearchParams();
  const { sessionState, clearSession } = useSession();
  useTheme();

  // Get session ID from URL params or session context
  const sessionId = searchParams?.get('sessionId') || sessionState?.id;

  // Handle session cleanup for restart
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

  // If no session ID, show error state
  if (!sessionId) {
    return (
      <main
        className="result-page min-h-screen flex items-center justify-center p-8 bg-surface"
        data-testid="error-container"
      >
        <div className="max-w-md space-y-5 text-center text-white/80">
          <h1 className="text-2xl font-semibold text-white">
            セッションが無効です
          </h1>
          <p data-testid="error-message">セッションIDが見つかりません。新しい診断を開始してください。</p>
          <button
            onClick={handleRestart}
            className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent/90"
            data-testid="restart-button"
          >
            はじめに戻る
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="result-page min-h-screen bg-surface" data-testid="result-container">
      <Suspense fallback={<LoadingFallback />}>
        <ResultScreen
          sessionId={sessionId}
          apiClient={{
            getResult: async (sessionId: string) => {
              const response = await fetch(`/api/sessions/${sessionId}/result`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
              });
              if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                
                // Create structured error for ResultScreen to handle
                const error = new Error(`Failed to get result: ${response.statusText}`);
                
                // Add error codes that ResultScreen expects
                if (response.status === 404) {
                  (error as any).code = 'SESSION_NOT_FOUND';
                } else if (response.status === 400 && errorData.error_code === 'SESSION_NOT_COMPLETED') {
                  (error as any).code = 'SESSION_NOT_COMPLETED';
                } else if (response.status >= 500) {
                  (error as any).code = 'NETWORK_ERROR';
                }
                
                throw error;
              }
              
              const data = await response.json();
              
              // Update session context with result state
              if (sessionState) {
                sessionState.state = 'RESULT';
                sessionState.completedAt = data.completedAt;
              }
              
              return data;
            }
          }}
        />
      </Suspense>
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

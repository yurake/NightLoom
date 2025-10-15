"use client";

import { useEffect, useState } from "react";
import { useTheme } from "../theme/ThemeProvider";
import { useSession, sessionActions } from "../state/SessionContext";
import { sessionClient, SessionAPIError } from "../services/sessionClient";
import type { Session } from "../types/session";

interface BootstrapData {
  sessionId: string;
  axes: Array<{
    id: string;
    name: string;
    description: string;
    direction: string;
  }>;
  keywordCandidates: string[];
  initialCharacter: string;
  themeId: string;
  fallbackUsed?: boolean;
}

export default function PlayPage() {
  const { themeId, setThemeId } = useTheme();
  const { state, dispatch } = useSession();
  
  // Bootstrap state
  const [bootstrapData, setBootstrapData] = useState<BootstrapData | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  
  // Keyword selection state
  const [customKeyword, setCustomKeyword] = useState("");
  const [isSubmittingKeyword, setIsSubmittingKeyword] = useState(false);
  const [keywordError, setKeywordError] = useState<string | null>(null);

  // Start bootstrap on mount
  useEffect(() => {
    startBootstrap();
  }, []);

  const startBootstrap = async () => {
    try {
      setIsBootstrapping(true);
      setBootstrapError(null);
      dispatch(sessionActions.setLoading(true));

      const response = await sessionClient.bootstrap();
      
      // Create session object for context
      const session: Session = {
        id: response.sessionId,
        state: 'INIT',
        initialCharacter: response.initialCharacter,
        keywordCandidates: response.keywordCandidates,
        selectedKeyword: undefined,
        themeId: response.themeId,
        scenes: [],
        choices: [],
        rawScores: {},
        normalizedScores: {},
        typeProfiles: [],
        fallbackFlags: response.fallbackUsed ? ['BOOTSTRAP_FALLBACK'] : [],
        createdAt: new Date().toISOString()
      };

      setBootstrapData(response);
      dispatch(sessionActions.bootstrapSuccess(session));
      
      // Apply theme from bootstrap response
      if (response.themeId !== themeId) {
        setThemeId(response.themeId as any);
      }
      
    } catch (error) {
      console.error('Bootstrap failed:', error);
      const errorMessage = error instanceof SessionAPIError 
        ? error.message 
        : 'ネットワークエラーが発生しました';
      
      setBootstrapError(errorMessage);
      dispatch(sessionActions.setError(errorMessage));
    } finally {
      setIsBootstrapping(false);
      dispatch(sessionActions.setLoading(false));
    }
  };

  const handleKeywordSelection = async (keyword: string, source: 'suggestion' | 'manual') => {
    if (!bootstrapData) return;
    
    try {
      setIsSubmittingKeyword(true);
      setKeywordError(null);
      dispatch(sessionActions.setLoading(true));

      const response = await sessionClient.confirmKeyword(
        bootstrapData.sessionId,
        keyword,
        source
      );

      dispatch(sessionActions.keywordConfirmed(keyword, response.scene));
      
    } catch (error) {
      console.error('Keyword confirmation failed:', error);
      const errorMessage = error instanceof SessionAPIError 
        ? error.message 
        : 'キーワードの確定に失敗しました';
      
      setKeywordError(errorMessage);
      dispatch(sessionActions.setError(errorMessage));
    } finally {
      setIsSubmittingKeyword(false);
      dispatch(sessionActions.setLoading(false));
    }
  };

  const handleSuggestedKeyword = (keyword: string) => {
    handleKeywordSelection(keyword, 'suggestion');
  };

  const handleCustomKeywordSubmit = () => {
    if (customKeyword.trim()) {
      handleKeywordSelection(customKeyword.trim(), 'manual');
    }
  };

  const isCustomKeywordValid = () => {
    const trimmed = customKeyword.trim();
    // Use Array.from to properly count Unicode characters
    const charCount = Array.from(trimmed).length;
    return charCount > 0 && charCount <= 20;
  };

  // Loading state
  if (isBootstrapping) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8">
        <div 
          className="text-center"
          data-testid="bootstrap-loading"
          aria-live="polite"
        >
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto" />
          <p className="text-lg text-white/80">診断を準備中...</p>
          <p className="text-sm text-white/60 mt-2">読み込み中</p>
        </div>
      </main>
    );
  }

  // Error state
  if (bootstrapError) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8">
        <div 
          className="text-center max-w-md"
          data-testid="bootstrap-error"
          aria-live="assertive"
        >
          <div className="mb-4 text-red-400 text-4xl">⚠️</div>
          <h2 className="text-xl font-medium mb-4 text-white">エラーが発生しました</h2>
          <p className="text-white/70 mb-6" data-testid="error-message">
            {bootstrapError}
          </p>
          <button
            onClick={startBootstrap}
            className="rounded-full bg-accent px-6 py-3 text-surface font-medium hover:bg-accent/90 transition-colors"
            data-testid="retry-button"
          >
            再試行
          </button>
        </div>
      </main>
    );
  }

  // Scene display (when session is in PLAY state)
  if (state.session?.state === 'PLAY' && state.currentScene) {
    return (
      <main 
        className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 p-8"
        data-testid="scene-container"
        data-theme={themeId}
      >
        {/* Progress indicator */}
        <div className="flex items-center justify-between">
          <div 
            className="text-sm text-white/60"
            data-testid="progress-indicator"
          >
            <span data-testid="progress-text">
              {state.currentSceneIndex}/4
            </span>
          </div>
          <div 
            className="text-xs text-white/40"
            data-testid="session-debug-info"
            data-session-id={state.session.id}
          >
            Session: {state.session.id.slice(0, 8)}...
          </div>
        </div>

        {/* Scene content */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 shadow-lg backdrop-blur">
          <div className="mb-2">
            <span 
              className="text-lg font-medium text-accent"
              data-testid="scene-index"
            >
              {state.currentScene.sceneIndex}
            </span>
          </div>
          
          <div 
            className="text-lg leading-relaxed text-white mb-8"
            data-testid="scene-narrative"
          >
            {state.currentScene.narrative}
          </div>

          <div 
            className="space-y-3"
            data-testid="choice-options"
            role="group"
            aria-label="選択肢"
          >
            {state.currentScene.choices.map((choice, index) => (
              <button
                key={choice.id}
                className="w-full rounded-xl border border-white/20 bg-white/10 p-4 text-left hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={state.isLoading}
                onClick={() => {
                  // Handle choice selection - implement later
                  console.log('Choice selected:', choice.id);
                }}
                aria-label={`選択肢${index + 1}: ${choice.text}`}
              >
                <span className="text-white">{choice.text}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Loading indicator for scene transitions */}
        {state.isLoading && (
          <div 
            className="text-center py-4"
            data-testid="loading-indicator"
            aria-live="polite"
          >
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto mb-2" />
            <p className="text-sm text-white/70">次のシーンを準備中...</p>
          </div>
        )}
      </main>
    );
  }

  // Keyword selection screen (initial state)
  if (bootstrapData) {
    return (
      <main 
        className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 p-8"
        data-testid="theme-container"
        data-theme={themeId}
      >
        <header className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight mb-4">NightLoom</h1>
          <div className="mb-6">
            <div 
              className="text-xl mb-2"
              data-testid="initial-character"
            >
              「{bootstrapData.initialCharacter}」
            </div>
            <p className="text-white/70">
              で始まる単語を選んでください
            </p>
          </div>
        </header>

        <section className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur">
          <h2 className="text-lg font-medium mb-4">提案キーワード</h2>
          
          <div 
            className="grid grid-cols-2 gap-3 mb-6"
            data-testid="keyword-candidates"
            role="group"
            aria-label="提案されたキーワード候補"
          >
            {bootstrapData.keywordCandidates.map((keyword, index) => (
              <button
                key={keyword}
                className="rounded-xl border border-white/20 bg-white/10 p-4 text-center hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => handleSuggestedKeyword(keyword)}
                disabled={isSubmittingKeyword}
                data-testid={`keyword-option-${index}`}
                aria-label={`キーワード候補: ${keyword}`}
                type="button"
              >
                <span className="text-white font-medium">{keyword}</span>
              </button>
            ))}
          </div>

          <div className="border-t border-white/10 pt-4">
            <h3 className="text-sm font-medium mb-3 text-white/80">または自由に入力</h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={customKeyword}
                onChange={(e) => setCustomKeyword(e.target.value)}
                placeholder={`${bootstrapData.initialCharacter}で始まる単語を入力`}
                className="flex-1 rounded-lg border border-white/20 bg-white/10 px-4 py-2 text-white placeholder-white/50 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                maxLength={20}
                disabled={isSubmittingKeyword}
                data-testid="custom-keyword-input"
                aria-label="カスタムキーワード入力"
                aria-describedby="keyword-help"
              />
              <button
                onClick={handleCustomKeywordSubmit}
                disabled={!isCustomKeywordValid() || isSubmittingKeyword}
                className="rounded-lg bg-accent px-4 py-2 text-surface font-medium hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="submit-custom-keyword"
                type="button"
              >
                決定
              </button>
            </div>
            <div 
              id="keyword-help" 
              className="text-xs text-white/60 mt-2"
            >
              1〜20文字で入力してください
            </div>
          </div>

          {keywordError && (
            <div 
              className="mt-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30"
              data-testid="error-message"
              role="alert"
            >
              <p className="text-red-300 text-sm">{keywordError}</p>
            </div>
          )}
        </section>

        {/* Screen reader announcement area */}
        <div 
          className="sr-only"
          aria-live="polite"
          data-testid="screen-reader-announcement"
        >
          {isSubmittingKeyword && "キーワードを確定中です"}
          {bootstrapData.fallbackUsed && "代替データを使用して診断を開始します"}
        </div>

        {/* Loading indicator for keyword submission */}
        {isSubmittingKeyword && (
          <div 
            className="text-center py-4"
            data-testid="loading-indicator"
            aria-live="polite"
          >
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto mb-2" />
            <p className="text-sm text-white/70">診断を開始中...</p>
          </div>
        )}
      </main>
    );
  }

  // Fallback state
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-4">NightLoom</h1>
        <p className="text-white/70 mb-6">診断を準備しています...</p>
        <button
          onClick={startBootstrap}
          className="rounded-full bg-accent px-6 py-3 text-surface font-medium hover:bg-accent/90 transition-colors"
          data-testid="bootstrap-start-button"
        >
          診断を始める
        </button>
      </div>
    </main>
  );
}

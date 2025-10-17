"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "../../theme/ThemeProvider";
import { useSession, sessionActions } from "../../state/SessionContext";
import { sessionClient, SessionAPIError } from "../../services/sessionClient";
import type { Session } from "../../types/session";
import SkipLinks from "../../components/SkipLinks";

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
  const router = useRouter();
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
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const [isSubmittingChoice, setIsSubmittingChoice] = useState(false);

  const startBootstrap = useCallback(async (retryCount = 0) => {
    const maxRetries = 3;
    const baseDelay = 100; // Reduced to 100ms for faster test execution

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

      // Clear loading state on success
      setIsBootstrapping(false);
      dispatch(sessionActions.setLoading(false));
      
    } catch (error) {
      console.error('Bootstrap failed:', error);
      
      if (retryCount < maxRetries) {
        // Exponential backoff: baseDelay * 2^retryCount
        const delay = baseDelay * Math.pow(2, retryCount);
        console.log(`Retrying bootstrap in ${delay}ms (attempt ${retryCount + 1}/${maxRetries + 1})`);
        
        setTimeout(() => {
          void startBootstrap(retryCount + 1);
        }, delay);
        return;
      }
      
      const errorMessage = (error as any)?.name === 'SessionAPIError'
        ? (error as SessionAPIError).message
        : 'ネットワークエラーが発生しました';
      
      setBootstrapError(errorMessage);
      dispatch(sessionActions.setError(errorMessage));
      setIsBootstrapping(false);
      dispatch(sessionActions.setLoading(false));
    }
  }, [dispatch, themeId, setThemeId]);

  // Start bootstrap on mount
  useEffect(() => {
    void startBootstrap();
  }, [startBootstrap]);

  useEffect(() => {
    setSelectedChoiceId(null);
    setSceneError(null);
  }, [state.currentScene?.sceneIndex]);

  const handleRetryBootstrap = () => {
    void startBootstrap();
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
      const errorMessage = (error as any)?.name === 'SessionAPIError'
        ? (error as SessionAPIError).message
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

  const handleChoiceSelect = async (choiceId: string) => {
    if (!state.session || !state.currentScene) return;
    if (isSubmittingChoice) return;

    setSelectedChoiceId(choiceId);
    setSceneError(null);
    setIsSubmittingChoice(true);
    dispatch(sessionActions.setLoading(true));

    try {
      const response = await sessionClient.submitChoice(
        state.session.id,
        state.currentScene.sceneIndex,
        choiceId
      );
      dispatch(
        sessionActions.choiceSubmitted(
          state.currentScene.sceneIndex,
          choiceId,
          response.nextScene || undefined
        )
      );

      if (response.nextScene) {
        setSelectedChoiceId(null);
      } else {
        router.push(`/play/result?sessionId=${state.session.id}`);
      }
    } catch (error) {
      console.error('Choice submission failed:', error);
      const message =
        error instanceof SessionAPIError
          ? error.message || '選択の送信に失敗しました'
          : '選択の送信に失敗しました';
      setSceneError(message);
      dispatch(sessionActions.setError(message));
    } finally {
      setIsSubmittingChoice(false);
      dispatch(sessionActions.setLoading(false));
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
      <>
        <SkipLinks />
        <main
          id="main-content"
          className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8"
          tabIndex={-1}
        >
          <div
            className="text-center"
            data-testid="bootstrap-loading"
            aria-live="polite"
            role="status"
          >
            <div
              className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto"
              aria-hidden="true"
            />
            <h1 className="sr-only">NightLoom 診断システム</h1>
            <p className="text-lg text-white/80">診断を準備中...</p>
            <p className="text-sm text-white/60 mt-2">読み込み中</p>
            
            {/* スクリーンリーダー向けの詳細説明 */}
            <div className="sr-only">
              <p>診断システムを初期化しています。しばらくお待ちください。</p>
            </div>
          </div>
        </main>
      </>
    );
  }

  // Error state
  if (bootstrapError) {
    return (
      <>
        <SkipLinks />
        <main
          id="main-content"
          className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8"
          tabIndex={-1}
        >
          <div
            className="text-center max-w-md"
            data-testid="bootstrap-error"
            aria-live="assertive"
            role="alert"
          >
            <div className="mb-4 text-red-400 text-4xl" aria-hidden="true">⚠️</div>
            <h1 className="text-xl font-medium mb-4 text-white">エラーが発生しました</h1>
            <p className="text-white/70 mb-6" data-testid="error-message">
              {bootstrapError}
            </p>
            <button
              onClick={handleRetryBootstrap}
              className="rounded-full bg-accent px-6 py-3 text-surface font-medium hover:bg-accent/90 transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
              data-testid="retry-button"
              aria-describedby="retry-help"
            >
              再試行
            </button>
            <div id="retry-help" className="sr-only">
              診断システムの初期化を再度試行します
            </div>
          </div>
        </main>
      </>
    );
  }

  // Scene display (when session is in PLAY state)
  if (state.session?.state === 'PLAY' && state.currentScene) {
    return (
      <>
        <SkipLinks />
        <main
          id="main-content"
          className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 p-8"
          data-testid="scene-container"
          data-theme={themeId}
          tabIndex={-1}
        >
          {/* Page title for screen readers */}
          <h1 className="sr-only">
            NightLoom 診断 - シーン {state.currentScene.sceneIndex}
          </h1>

          {/* Progress indicator */}
          <div className="flex items-center justify-between">
            <progress
              className="sr-only"
              data-testid="progress-bar"
              value={((state.currentSceneIndex || 1) / 4) * 100}
              max="100"
            />
            <div
              className="text-sm text-white/60"
              data-testid="progress-indicator"
              role="status"
              aria-label={`進行状況: ${state.currentSceneIndex}シーン目、全4シーン中`}
            >
              <span data-testid="progress-text">
                {state.currentSceneIndex}/4
              </span>
            </div>
            <div
              className="text-xs text-white/40"
              data-testid="session-debug-info"
              data-session-id={state.session.id}
              aria-hidden="true"
            >
              Session: {state.session.id.slice(0, 8)}...
            </div>
          </div>

          {/* Scene content */}
          <section
            className="rounded-2xl border border-white/10 bg-white/5 p-8 shadow-lg backdrop-blur"
            aria-labelledby="scene-heading"
          >
            <header className="mb-8">
              <h2
                id="scene-heading"
                className="text-lg font-medium text-accent mb-2"
                data-testid="scene-index"
              >
                {state.currentScene?.sceneIndex || 0}
              </h2>
              <div className="sr-only" data-testid="scene-counter">
                シーン {state.currentScene?.sceneIndex || 0}
              </div>
              
              <div
                className="text-lg leading-relaxed text-white"
                data-testid="scene-narrative"
                role="text"
              >
                {state.currentScene.narrative}
              </div>
            </header>

            <div
              id="choice-options"
              className="space-y-3"
              data-testid="choice-options"
              role="radiogroup"
              aria-labelledby="choices-heading"
            >
              <h3 id="choices-heading" className="sr-only">
                選択肢を選んでください
              </h3>
              
              {state.currentScene.choices.map((choice, index) => (
                <button
                  key={choice.id}
                  className={`w-full rounded-xl border ${
                    selectedChoiceId === choice.id
                      ? 'border-accent bg-accent/20'
                      : 'border-white/20 bg-white/10 hover:bg-white/20'
                  } p-4 text-left transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2`}
                  disabled={state.isLoading || isSubmittingChoice}
                  onClick={() => handleChoiceSelect(choice.id)}
                  role="radio"
                  aria-checked={selectedChoiceId === choice.id}
                  aria-label={`選択肢${index + 1}: ${choice.text}`}
                  aria-describedby={`choice-help-${choice.id}`}
                  data-selected={selectedChoiceId === choice.id}
                  data-testid={`choice-${state.currentScene?.sceneIndex || 0}-${index + 1}`}
                >
                  <span className="text-white">{choice.text}</span>
                  <div id={`choice-help-${choice.id}`} className="sr-only">
                    選択肢{index + 1}を選択するには、Enterキーまたはスペースキーを押してください
                  </div>
                </button>
              ))}
            </div>

            {sceneError && (
              <div
                className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200"
                role="alert"
                aria-live="assertive"
                data-testid="scene-error"
              >
                {sceneError}
              </div>
            )}

            {/* 操作説明 */}
            <div className="mt-6 text-center">
              <p className="text-sm text-white/60">
                選択肢を選んでください
              </p>
              <div className="sr-only">
                <p>矢印キーで選択肢間を移動できます。Enterキーまたはスペースキーで選択を確定してください。</p>
              </div>
            </div>
          </section>

          {/* Loading indicator for scene transitions */}
          {state.isLoading && (
            <div
              className="text-center py-4"
              data-testid="loading-indicator"
              aria-live="polite"
              role="status"
            >
              <div
                className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto mb-2"
                aria-hidden="true"
              />
              <p className="text-sm text-white/70">次のシーンを準備中...</p>
            </div>
          )}

          {/* Screen reader announcements */}
          <div
            className="sr-only"
            aria-live="polite"
            role="status"
          >
            {state.currentScene && `シーン${state.currentScene.sceneIndex}が読み込まれました`}
          </div>
        </main>
      </>
    );
  }

  // Keyword selection screen (initial state)
  if (bootstrapData) {
    return (
      <>
        <SkipLinks />
        <main
          id="main-content"
          className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 p-8"
          data-testid="theme-container"
          data-theme={themeId}
          tabIndex={-1}
        >
          <header className="text-center">
            <h1 className="text-3xl font-semibold tracking-tight mb-4">NightLoom</h1>
            <div className="mb-6">
              <div
                className="text-xl mb-2"
                data-testid="initial-character"
                role="text"
                aria-label={`頭文字: ${bootstrapData.initialCharacter}`}
              >
                「{bootstrapData.initialCharacter}」
                で始まる単語を選んでください
              </div>
              
              {/* スクリーンリーダー向けの詳細説明 */}
              <div className="sr-only">
                <p>
                  診断を開始するため、「{bootstrapData.initialCharacter}」で始まるキーワードを選択してください。
                  提案されたキーワードから選ぶか、独自のキーワードを入力できます。
                </p>
              </div>
            </div>
          </header>

          <section
            className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur"
            aria-labelledby="keyword-section-heading"
          >
            <h2
              id="keyword-section-heading"
              className="text-lg font-medium mb-4"
            >
              提案キーワード
            </h2>
            
            <div
              className="grid grid-cols-2 gap-3 mb-6"
              data-testid="keyword-candidates"
              role="radiogroup"
              aria-labelledby="suggested-keywords-heading"
              aria-describedby="suggested-keywords-help"
            >
              <h3 id="suggested-keywords-heading" className="sr-only">
                提案されたキーワード候補
              </h3>
              <div id="suggested-keywords-help" className="sr-only">
                以下のキーワードから1つを選択してください。矢印キーで移動、Enterキーまたはスペースキーで選択できます。
              </div>
              
              {bootstrapData.keywordCandidates.map((keyword, index) => (
                <button
                  key={keyword}
                  className="rounded-xl border border-white/20 bg-white/10 p-4 text-center hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                  onClick={() => handleSuggestedKeyword(keyword)}
                  disabled={isSubmittingKeyword}
                  data-testid={`keyword-option-${index}`}
                  role="radio"
                  aria-checked="false"
                  aria-label={`キーワード候補${index + 1}: ${keyword}`}
                  aria-describedby={`keyword-description-${index}`}
                  type="button"
                >
                  <span className="text-white font-medium">{keyword}</span>
                  <div id={`keyword-description-${index}`} className="sr-only">
                    「{keyword}」を診断キーワードとして使用します
                  </div>
                </button>
              ))}
            </div>

            <div className="border-t border-white/10 pt-4">
              <h3 className="text-sm font-medium mb-3 text-white/80">または自由に入力</h3>
              <div className="flex gap-3" role="group" aria-labelledby="custom-input-heading">
                <h4 id="custom-input-heading" className="sr-only">カスタムキーワード入力</h4>
                
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
                  aria-describedby="keyword-help custom-input-instructions"
                />
                <button
                  onClick={handleCustomKeywordSubmit}
                  disabled={!isCustomKeywordValid() || isSubmittingKeyword}
                  className="rounded-lg bg-accent px-4 py-2 text-surface font-medium hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                  data-testid="submit-custom-keyword"
                  type="button"
                  aria-describedby="submit-help"
                >
                  決定
                </button>
                
                <div id="submit-help" className="sr-only">
                  入力したキーワードで診断を開始します
                </div>
                <div id="custom-input-instructions" className="sr-only">
                  「{bootstrapData.initialCharacter}」で始まる1文字以上20文字以下のキーワードを入力してください
                </div>
              </div>
              
              <div
                id="keyword-help"
                className="text-xs text-white/60 mt-2"
                role="status"
                aria-live="polite"
              >
                1〜20文字で入力してください
                {customKeyword && (
                  <span className="ml-2">
                    現在{Array.from(customKeyword.trim()).length}文字
                  </span>
                )}
              </div>
            </div>

            {keywordError && (
              <div
                className="mt-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30"
                data-testid="error-message"
                role="alert"
                aria-live="assertive"
              >
                <h4 className="sr-only">エラー</h4>
                <p className="text-red-300 text-sm">{keywordError}</p>
              </div>
            )}
          </section>

          {/* Screen reader announcement area */}
          <div
            className="sr-only"
            aria-live="polite"
            role="status"
            data-testid="screen-reader-announcement"
          >
            {isSubmittingKeyword && "キーワードを確定中です。しばらくお待ちください。"}
            {bootstrapData.fallbackUsed && "代替データを使用して診断を開始します"}
            {bootstrapData && `診断が準備されました。「${bootstrapData.initialCharacter}」で始まるキーワードを選択してください。`}
          </div>

          {/* Loading indicator for keyword submission */}
          {isSubmittingKeyword && (
            <div
              className="text-center py-4"
              data-testid="loading-indicator"
              aria-live="polite"
              role="status"
            >
              <div
                className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent mx-auto mb-2"
                aria-hidden="true"
              />
              <p className="text-sm text-white/70">診断を開始中...</p>
            </div>
          )}
        </main>
      </>
    );
  }

  // Fallback state
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-4">NightLoom</h1>
        <p className="text-white/70 mb-6">診断を準備しています...</p>
        <button
          onClick={handleRetryBootstrap}
          className="rounded-full bg-accent px-6 py-3 text-surface font-medium hover:bg-accent/90 transition-colors"
          data-testid="bootstrap-start-button"
        >
          診断を始める
        </button>
      </div>
    </main>
  );
}

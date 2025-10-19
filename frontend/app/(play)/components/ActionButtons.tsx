/**
 * ActionButtons コンポーネント
 * 
 * @description 結果画面で使用されるアクションボタン群を提供
 * 再診断とリトライ機能を持つボタンコンポーネント
 */

import React, { useState, useCallback } from 'react';

// ActionButtons コンポーネント関連の型定義
export interface ActionButtonsProps {
  /**
   * 再診断開始時のコールバック
   * @description セッションクリーンアップ後にホーム画面へのナビゲーションを行う
   */
  onRestart: () => void | Promise<void>;
  
  /**
   * リトライ実行時のコールバック（オプション）
   * @description エラー状態からの復旧時に結果再取得を行う
   */
  onRetry?: () => void | Promise<void>;
  
  /**
   * ローディング状態
   * @description 親コンポーネントから渡される外部ローディング状態
   */
  isLoading?: boolean;
  
  /**
   * ボタン無効化状態
   * @description エラー時やその他の理由でボタンを無効化する
   */
  isDisabled?: boolean;
  
  /**
   * ボタンスタイルバリアント
   * @description primary（青系）またはsecondary（グレー系）のスタイル
   */
  variant?: 'primary' | 'secondary';
  
  /**
   * 追加CSSクラス
   * @description レスポンシブ対応やレイアウト調整用のクラス
   */
  className?: string;
  
  /**
   * aria-describedby属性値
   * @description アクセシビリティ向上のためのARIA属性
   */
  ariaDescribedBy?: string;
}

export interface ActionButtonsState {
  /**
   * 内部ローディング状態
   * @description コンポーネント内部で管理されるローディング状態
   */
  internalLoading: boolean;
  
  /**
   * エラー状態
   * @description 非同期処理中に発生したエラーメッセージ
   */
  error: string | null;
}

/**
 * ActionButtons コンポーネント
 *
 * @description 結果画面で使用される再診断・リトライ機能を提供するボタンコンポーネント
 *
 * @features
 * - 再診断ボタン（セッションクリーンアップ + ホーム遷移）
 * - リトライボタン（エラー時の結果再取得、オプション表示）
 * - 内部・外部ローディング状態の統合管理
 * - エラーハンドリングと表示
 * - キーボードアクセシビリティ対応（Enter、Space）
 * - レスポンシブデザイン対応
 *
 * @accessibility
 * - ARIA role, aria-label, aria-describedby属性
 * - aria-busy状態の管理
 * - live region によるエラーメッセージ通知
 * - tabIndex制御による適切なフォーカス管理
 * - キーボードナビゲーション完全対応
 *
 * @styling
 * - primary variant: 青系グラデーション（再診断用）
 * - secondary variant: グレー系（リトライ用）
 * - 無効化時: グレーアウトとcursor-not-allowed
 * - focus状態: ring outline による視覚的フィードバック
 *
 * @example
 * ```tsx
 * // 基本的な使用（再診断のみ）
 * <ActionButtons
 *   onRestart={handleRestart}
 *   isLoading={isLoading}
 *   className="w-full justify-center"
 * />
 *
 * // リトライ機能付き
 * <ActionButtons
 *   onRestart={handleRestart}
 *   onRetry={handleRetry}
 *   isDisabled={hasError}
 *   variant="secondary"
 *   ariaDescribedBy="help-text"
 * />
 * ```
 *
 * @param props - ActionButtonsProps
 * @returns JSX要素
 */
export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onRestart,
  onRetry,
  isLoading = false,
  isDisabled = false,
  variant = 'primary',
  className = '',
  ariaDescribedBy,
}) => {
  // 内部状態管理
  const [internalState, setInternalState] = useState<ActionButtonsState>({
    internalLoading: false,
    error: null,
  });

  // ボタンが無効化されているかの判定
  const isButtonDisabled = isLoading || isDisabled || internalState.internalLoading;

  // 再診断ボタンクリックハンドラー
  const handleRestartClick = useCallback(async () => {
    if (isButtonDisabled || !onRestart) return;

    try {
      setInternalState(prev => ({ ...prev, internalLoading: true, error: null }));
      await onRestart();
    } catch (error) {
      setInternalState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'エラーが発生しました',
      }));
    } finally {
      setInternalState(prev => ({ ...prev, internalLoading: false }));
    }
  }, [onRestart, isButtonDisabled]);

  // リトライボタンクリックハンドラー
  const handleRetryClick = useCallback(async () => {
    if (isButtonDisabled || !onRetry) return;

    try {
      setInternalState(prev => ({ ...prev, internalLoading: true, error: null }));
      await onRetry();
    } catch (error) {
      setInternalState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'エラーが発生しました',
      }));
    } finally {
      setInternalState(prev => ({ ...prev, internalLoading: false }));
    }
  }, [onRetry, isButtonDisabled]);

  // キーボードイベントハンドラー
  const handleKeyDown = useCallback((handler: () => void) => 
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handler();
      }
    }, []
  );

  // バリアント別のスタイルクラス
  const getButtonStyles = (isPrimary: boolean) => {
    const baseStyles = 'px-6 py-3 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    if (isButtonDisabled) {
      return `${baseStyles} bg-gray-300 text-gray-500 cursor-not-allowed`;
    }

    if (isPrimary || variant === 'primary') {
      return `${baseStyles} primary bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500`;
    }
    
    return `${baseStyles} secondary bg-gray-200 hover:bg-gray-300 text-gray-800 focus:ring-gray-500`;
  };

  // ローディングインジケーター
  const LoadingIndicator = () => (
    <div
      data-testid="loading-indicator"
      className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2"
      role="status"
      aria-label="読み込み中"
    />
  );

  const showLoading = isLoading || internalState.internalLoading;

  return (
    <div
      data-testid="action-buttons"
      className={`flex gap-4 items-center ${className}`}
      aria-busy={showLoading}
    >
      {/* 再診断ボタン */}
      <button
        data-testid="restart-button"
        onClick={handleRestartClick}
        onKeyDown={handleKeyDown(handleRestartClick)}
        disabled={isButtonDisabled}
        className={getButtonStyles(true)}
        aria-label="再診断を開始する"
        aria-describedby={ariaDescribedBy}
        aria-disabled={isButtonDisabled}
        role="button"
        tabIndex={isButtonDisabled ? -1 : 0}
      >
        {showLoading && <LoadingIndicator />}
        もう一度診断する
      </button>

      {/* リトライボタン（onRetry が提供された場合のみ表示） */}
      {onRetry && (
        <button
          data-testid="retry-button"
          onClick={handleRetryClick}
          onKeyDown={handleKeyDown(handleRetryClick)}
          disabled={isButtonDisabled}
          className={getButtonStyles(false)}
          aria-label="リトライを実行する"
          aria-disabled={isButtonDisabled}
          role="button"
          tabIndex={isButtonDisabled ? -1 : 0}
        >
          {showLoading && <LoadingIndicator />}
          リトライ
        </button>
      )}

      {/* ローディングテキスト */}
      {showLoading && (
        <span className="text-gray-600 text-sm">
          処理中...
        </span>
      )}

      {/* エラーメッセージ */}
      {internalState.error && (
        <div
          data-testid="error-message"
          className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-md"
          role="alert"
          aria-live="polite"
        >
          {internalState.error}
        </div>
      )}
    </div>
  );
};

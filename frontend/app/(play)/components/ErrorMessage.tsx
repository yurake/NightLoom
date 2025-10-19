/**
 * ErrorMessage Component
 * 
 * エラー状態の表示を行うコンポーネント
 * エラーコード別にユーザーフレンドリーなメッセージを表示
 */

import React from 'react';

interface ErrorMessageProps {
  /** エラーコード */
  errorCode?: string;
  /** カスタムエラーメッセージ */
  message?: string;
  /** 再試行ボタンのコールバック */
  onRetry?: () => void;
  /** 追加のCSSクラス */
  className?: string;
}

const ERROR_MESSAGES: Record<string, string> = {
  SESSION_NOT_FOUND: 'セッションが見つかりません。新しい診断を開始してください。',
  SESSION_NOT_COMPLETED: '診断が完了していません。診断を最後まで進めてください。',
  TYPE_GEN_FAILED: 'タイプ生成に失敗しました。しばらく待ってから再度お試しください。',
  NETWORK_ERROR: 'ネットワークエラーが発生しました。接続を確認してください。',
  UNKNOWN_ERROR: '予期しないエラーが発生しました。',
};

/**
 * ErrorMessage コンポーネント
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  errorCode,
  message,
  onRetry,
  className = '',
}) => {
  const displayMessage = message || ERROR_MESSAGES[errorCode || 'UNKNOWN_ERROR'] || ERROR_MESSAGES.UNKNOWN_ERROR;
  
  return (
    <div 
      className={`
        flex flex-col items-center justify-center p-6 bg-red-50 border border-red-200 rounded-lg
        text-center space-y-4 ${className}
      `}
      role="alert"
      aria-live="polite"
      data-testid="error-message"
    >
      {/* エラーアイコン */}
      <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
        <svg
          className="w-6 h-6 text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      
      {/* エラーメッセージ */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-red-800">
          エラーが発生しました
        </h3>
        <p className="text-red-700 max-w-md">
          {displayMessage}
        </p>
        {errorCode && (
          <p className="text-sm text-red-600 font-mono">
            エラーコード: {errorCode}
          </p>
        )}
      </div>
      
      {/* 再試行ボタン */}
      {onRetry && (
        <button
          onClick={onRetry}
          className="
            px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md
            transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
          "
          aria-label="エラー状態を解決するため再試行する"
          data-testid="retry-button"
        >
          再試行
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;

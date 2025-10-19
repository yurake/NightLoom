/**
 * Loading state components for NightLoom diagnosis flow
 * Provides consistent loading indicators and error states
 */

'use client';

import React from 'react';
import { useTheme } from '../../theme/ThemeProvider';

interface LoadingStateProps {
  message?: string;
  variant?: 'spinner' | 'skeleton' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = '読み込み中...',
  variant = 'spinner',
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  if (variant === 'spinner') {
    return (
      <div 
        className={`loading-state flex flex-col items-center justify-center p-6 text-white/80 ${className}`}
        data-testid="loading-indicator"
      >
        <div
          className={`animate-spin rounded-full border-2 border-t-transparent border-accent ${sizeClasses[size]} mb-4`}
        />
        <p 
          className="text-center font-medium text-white/80"
        >
          {message}
        </p>
      </div>
    );
  }

  if (variant === 'skeleton') {
    return (
      <div 
        className={`loading-skeleton space-y-4 p-6 ${className}`}
        data-testid="loading-skeleton"
      >
        <div 
          className="skeleton-line h-4 rounded animate-pulse bg-white/10"
        />
        <div 
          className="skeleton-line h-4 rounded animate-pulse w-3/4 bg-white/10"
        />
        <div 
          className="skeleton-line h-4 rounded animate-pulse w-1/2 bg-white/10"
        />
      </div>
    );
  }

  if (variant === 'pulse') {
    return (
      <div 
        className={`loading-pulse flex items-center justify-center p-6 ${className}`}
        data-testid="loading-pulse"
      >
        <div className="flex space-x-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-full animate-pulse bg-accent"
              style={{
                animationDelay: `${i * 0.2}s`,
                animationDuration: '1s'
              }}
            />
          ))}
        </div>
        <p 
          className="ml-4 font-medium text-white/80"
        >
          {message}
        </p>
      </div>
    );
  }

  return null;
};

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'エラーが発生しました',
  message,
  onRetry,
  retryLabel = '再試行',
  variant = 'error',
  className = ''
}) => {
  const getIcon = () => {
    switch (variant) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const getIconColor = () => {
    switch (variant) {
      case 'warning':
        return '#f59e0b';
      case 'info':
        return '#3b82f6';
      default:
        return '#ef4444';
    }
  };

  return (
    <div 
      className={`error-state flex flex-col items-center justify-center p-6 text-center ${className}`}
      data-testid="error-container"
    >
      <div 
        className="error-icon text-6xl mb-4"
        style={{ color: getIconColor() }}
      >
        {getIcon()}
      </div>
      
      <h2 
        className="error-title text-xl font-semibold mb-2 text-white"
      >
        {title}
      </h2>
      
      <p 
        className="error-message text-base mb-6 max-w-md leading-relaxed text-white/80"
        data-testid="error-message"
      >
        {message}
      </p>
      
      {onRetry && (
        <button
          onClick={onRetry}
          className="retry-button px-6 py-2 rounded-lg font-medium transition-colors hover:shadow-md bg-accent text-white"
          data-testid="retry-button"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
};

interface NetworkErrorStateProps {
  onRetry?: () => void;
  className?: string;
}

export const NetworkErrorState: React.FC<NetworkErrorStateProps> = ({
  onRetry,
  className = ''
}) => (
  <ErrorState
    title="ネットワークエラー"
    message="インターネット接続を確認してください。問題が続く場合は、しばらく待ってから再試行してください。"
    onRetry={onRetry}
    variant="warning"
    className={className}
  />
);

interface SessionExpiredStateProps {
  onRestart?: () => void;
  className?: string;
}

export const SessionExpiredState: React.FC<SessionExpiredStateProps> = ({
  onRestart,
  className = ''
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <div
      className={`error-state flex flex-col items-center justify-center p-6 text-center ${className}`}
      data-testid="error-container"
    >
      <div
        className="error-icon text-6xl mb-4"
        style={{ color: '#3b82f6' }}
      >
        ℹ️
      </div>
      
      <h2
        className="error-title text-xl font-semibold mb-2"
        style={{ color: currentTheme.text.primary }}
      >
        セッションが期限切れです
      </h2>
      
      <p
        className="error-message text-base mb-6 max-w-md leading-relaxed"
        style={{ color: currentTheme.text.secondary }}
        data-testid="error-message"
      >
        診断セッションの有効期限が切れました。診断を続けるか、新しい診断を開始してください。
      </p>
      
      <div className="flex flex-col gap-4">
        <button
          onClick={() => {/* 診断を続ける処理 */}}
          className="retry-button px-6 py-2 rounded-lg font-medium transition-colors hover:shadow-md"
          style={{
            backgroundColor: currentTheme.secondary,
            color: 'white'
          }}
          data-testid="continue-button"
        >
          診断を続ける
        </button>
        
        {onRestart && (
          <button
            onClick={onRestart}
            className="retry-button px-6 py-2 rounded-lg font-medium transition-colors hover:shadow-md"
            style={{
              backgroundColor: currentTheme.primary,
              color: 'white'
            }}
            data-testid="restart-button"
          >
            新しい診断を開始
          </button>
        )}
      </div>
    </div>
  );
};

interface ServiceUnavailableStateProps {
  onRetry?: () => void;
  className?: string;
}

export const ServiceUnavailableState: React.FC<ServiceUnavailableStateProps> = ({
  onRetry,
  className = ''
}) => (
  <ErrorState
    title="サービス一時停止中"
    message="診断サービスが一時的に利用できません。しばらく待ってから再試行してください。"
    onRetry={onRetry}
    retryLabel="再試行"
    variant="warning"
    className={className}
  />
);

// Scene-specific loading states
export const SceneLoadingState: React.FC<{ sceneIndex: number }> = ({ sceneIndex }) => (
  <LoadingState
    message={`シーン ${sceneIndex} を読み込み中...`}
    variant="spinner"
    size="lg"
    className="min-h-96"
  />
);

export const ChoiceSubmissionLoadingState: React.FC = () => (
  <LoadingState
    message="選択を送信中..."
    variant="pulse"
    size="md"
  />
);

export const ResultLoadingState: React.FC = () => (
  <LoadingState
    message="診断結果を生成中..."
    variant="spinner"
    size="lg"
    className="min-h-96"
  />
);

// Utility component for inline loading indicators
export const InlineLoading: React.FC<{ 
  message?: string; 
  size?: 'sm' | 'md';
  className?: string;
}> = ({ 
  message = '処理中...', 
  size = 'sm',
  className = ''
}) => {
  const { currentTheme } = useTheme();
  
  return (
    <div className={`inline-loading flex items-center ${className}`}>
      <div
        className={`animate-spin rounded-full border-2 border-t-transparent ${
          size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'
        } mr-2`}
        style={{ 
          borderColor: `${currentTheme.border} transparent ${currentTheme.primary} transparent` 
        }}
      />
      <span 
        className="text-sm"
        style={{ color: currentTheme.text.secondary }}
      >
        {message}
      </span>
    </div>
  );
};

// Hook for managing loading states
export function useLoadingState(initialState: boolean = false) {
  const [isLoading, setIsLoading] = React.useState(initialState);
  const [error, setError] = React.useState<string | null>(null);

  const startLoading = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const stopLoading = React.useCallback(() => {
    setIsLoading(false);
  }, []);

  const setErrorState = React.useCallback((errorMessage: string) => {
    setIsLoading(false);
    setError(errorMessage);
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const reset = React.useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setErrorState,
    clearError,
    reset
  };
}

export default LoadingState;

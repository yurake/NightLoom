/**
 * ProgressIndicator component for showing diagnosis progress
 * Displays current scene position and completion percentage
 */

'use client';

import React from 'react';
import { useTheme } from '../../theme/ThemeProvider';

interface ProgressIndicatorProps {
  currentScene: number;
  totalScenes: number;
  completedScenes?: number;
  className?: string;
  showPercentage?: boolean;
  showSceneNumbers?: boolean;
  variant?: 'bar' | 'dots' | 'steps';
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentScene,
  totalScenes = 4,
  completedScenes,
  className = '',
  showPercentage = true,
  showSceneNumbers = true,
  variant = 'bar'
}) => {
  const { currentTheme, themeId } = useTheme();
  
  // Calculate progress values
  const completed = completedScenes ?? Math.max(0, currentScene - 1);
  const progressPercentage = Math.min(100, (completed / totalScenes) * 100);
  const displayPercentage = Math.round(progressPercentage);

  // Bar variant (default)
  if (variant === 'bar') {
    return (
      <div className={`progress-indicator ${className}`} data-testid="progress-indicator">
        {/* Progress Header */}
        <div className="progress-header flex justify-between items-center mb-3">
          {showSceneNumbers && (
            <div className="progress-text">
              <span 
                className="text-sm font-medium"
                style={{ color: currentTheme.text.primary }}
                data-testid="progress-text"
              >
                {completed} / {totalScenes}
              </span>
            </div>
          )}
          
          {showPercentage && (
            <div className="progress-percentage">
              <span 
                className="text-sm font-medium"
                style={{ color: currentTheme.text.secondary }}
                data-testid="progress-percentage"
              >
                {displayPercentage}%
              </span>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div
            className="progress-bar-track h-2 rounded-full relative overflow-hidden"
            style={{ 
              backgroundColor: `${currentTheme.border}40`,
              borderRadius: '9999px'
            }}
            data-testid="progress-bar"
          >
            <div
              className="progress-bar-fill h-full transition-all duration-500 ease-out rounded-full"
              style={{
                width: `${progressPercentage}%`,
                backgroundColor: currentTheme.primary,
                borderRadius: '9999px'
              }}
              data-testid="progress-fill"
              role="progressbar"
              aria-valuenow={displayPercentage}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`診断進行状況: ${displayPercentage}%完了`}
            />
            
            {/* Glow effect for active progress */}
            {progressPercentage > 0 && progressPercentage < 100 && (
              <div
                className="progress-glow absolute top-0 right-0 h-full w-8 opacity-60"
                style={{
                  background: `linear-gradient(90deg, transparent, ${currentTheme.primary}60, transparent)`,
                  transform: 'translateX(-100%)',
                  animation: 'progress-shimmer 2s infinite'
                }}
              />
            )}
          </div>
        </div>

        {/* Scene Labels */}
        {showSceneNumbers && (
          <div className="progress-labels flex justify-between mt-2 text-xs">
            {Array.from({ length: totalScenes }, (_, index) => {
              const sceneNum = index + 1;
              const isCompleted = sceneNum <= completed;
              const isCurrent = sceneNum === currentScene;
              
              return (
                <span
                  key={sceneNum}
                  className={`progress-label ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}
                  style={{
                    color: isCompleted 
                      ? currentTheme.primary 
                      : isCurrent 
                        ? currentTheme.text.primary
                        : currentTheme.text.muted
                  }}
                  data-testid={`scene-label-${sceneNum}`}
                >
                  {sceneNum}
                </span>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // Dots variant
  if (variant === 'dots') {
    return (
      <div className={`progress-indicator dots-variant ${className}`} data-testid="progress-indicator">
        <div className="flex items-center justify-center space-x-3">
          {Array.from({ length: totalScenes }, (_, index) => {
            const sceneNum = index + 1;
            const isCompleted = sceneNum <= completed;
            const isCurrent = sceneNum === currentScene;
            
            return (
              <div
                key={sceneNum}
                className={`progress-dot w-4 h-4 rounded-full transition-all duration-300 ${
                  isCurrent ? 'ring-2 ring-offset-2' : ''
                }`}
                style={{
                  backgroundColor: isCompleted 
                    ? currentTheme.primary 
                    : isCurrent
                      ? `${currentTheme.primary}60`
                      : currentTheme.border,
                  ringColor: isCurrent ? currentTheme.primary : 'transparent',
                  transform: isCurrent ? 'scale(1.2)' : 'scale(1)'
                }}
                data-testid={`progress-dot-${sceneNum}`}
                aria-label={`シーン ${sceneNum} ${isCompleted ? '完了' : isCurrent ? '現在' : '未完了'}`}
              />
            );
          })}
        </div>
        
        {showPercentage && (
          <div className="text-center mt-3">
            <span 
              className="text-sm font-medium"
              style={{ color: currentTheme.text.secondary }}
              data-testid="progress-percentage"
            >
              {displayPercentage}% 完了
            </span>
          </div>
        )}
      </div>
    );
  }

  // Steps variant
  if (variant === 'steps') {
    return (
      <div className={`progress-indicator steps-variant ${className}`} data-testid="progress-indicator">
        <div className="flex items-center">
          {Array.from({ length: totalScenes }, (_, index) => {
            const sceneNum = index + 1;
            const isCompleted = sceneNum <= completed;
            const isCurrent = sceneNum === currentScene;
            const isLast = index === totalScenes - 1;
            
            return (
              <React.Fragment key={sceneNum}>
                {/* Step Circle */}
                <div className="flex flex-col items-center">
                  <div
                    className={`step-circle w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300 ${
                      isCurrent ? 'ring-2 ring-offset-2' : ''
                    }`}
                    style={{
                      backgroundColor: isCompleted 
                        ? currentTheme.primary 
                        : isCurrent
                          ? `${currentTheme.primary}60`
                          : currentTheme.border,
                      color: isCompleted || isCurrent ? 'white' : currentTheme.text.muted,
                      ringColor: isCurrent ? currentTheme.primary : 'transparent'
                    }}
                    data-testid={`step-${sceneNum}`}
                  >
                    {isCompleted ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      sceneNum
                    )}
                  </div>
                  
                  {/* Step Label */}
                  <span
                    className="step-label text-xs mt-1"
                    style={{
                      color: isCompleted 
                        ? currentTheme.primary 
                        : isCurrent 
                          ? currentTheme.text.primary
                          : currentTheme.text.muted
                    }}
                  >
                    シーン{sceneNum}
                  </span>
                </div>

                {/* Connector Line */}
                {!isLast && (
                  <div
                    className="step-connector flex-1 h-0.5 mx-2 transition-colors duration-300"
                    style={{
                      backgroundColor: sceneNum <= completed 
                        ? currentTheme.primary 
                        : currentTheme.border
                    }}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    );
  }

  return null;
};

// Utility component for compact progress display
export const CompactProgressIndicator: React.FC<{
  currentScene: number;
  totalScenes: number;
  className?: string;
}> = ({ currentScene, totalScenes, className = '' }) => {
  const { currentTheme } = useTheme();
  
  return (
    <div className={`compact-progress ${className}`} data-testid="compact-progress">
      <span 
        className="text-sm font-medium"
        style={{ color: currentTheme.text.secondary }}
      >
        {Math.max(0, currentScene - 1)} / {totalScenes} 完了
      </span>
    </div>
  );
};

// CSS styles (would typically be in a separate CSS file)
const progressStyles = `
@keyframes progress-shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}

.progress-indicator {
  user-select: none;
}

.progress-bar-track {
  position: relative;
  overflow: hidden;
}

.progress-dot {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-circle {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-connector {
  transition: background-color 0.3s ease;
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  .progress-bar-fill,
  .progress-dot,
  .step-circle,
  .step-connector {
    transition: none;
  }
  
  .progress-glow {
    display: none;
  }
}
`;

// Inject styles (in a real app, this would be in a CSS file)
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = progressStyles;
  document.head.appendChild(styleElement);
}

export default ProgressIndicator;

/**
 * ChoiceOptions component for displaying and handling choice selection
 * Used within Scene component for interactive choice selection
 */

'use client';

import React, { useState, useCallback } from 'react';
import { useTheme } from '@/app/theme/ThemeProvider';

interface Choice {
  id: string;
  text: string;
  weights: Record<string, number>;
}

interface ChoiceOptionsProps {
  choices: Choice[];
  selectedChoiceId?: string | null;
  onChoiceSelect: (choiceId: string) => void;
  disabled?: boolean;
  sceneIndex: number;
  className?: string;
}

export const ChoiceOptions: React.FC<ChoiceOptionsProps> = ({
  choices,
  selectedChoiceId,
  onChoiceSelect,
  disabled = false,
  sceneIndex,
  className = ''
}) => {
  const { currentTheme, themeId } = useTheme();
  const [hoveredChoice, setHoveredChoice] = useState<string | null>(null);

  const handleChoiceClick = useCallback((choiceId: string) => {
    if (disabled) return;
    onChoiceSelect(choiceId);
  }, [disabled, onChoiceSelect]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent, choiceId: string, index: number) => {
    if (disabled) return;
    
    const currentTarget = event.currentTarget as HTMLElement;
    
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        onChoiceSelect(choiceId);
        break;
        
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = (index + 1) % choices.length;
        const nextButton = document.querySelector(`[data-testid="choice-${sceneIndex}-${nextIndex + 1}"]`) as HTMLElement;
        nextButton?.focus();
        break;
        
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = index === 0 ? choices.length - 1 : index - 1;
        const prevButton = document.querySelector(`[data-testid="choice-${sceneIndex}-${prevIndex + 1}"]`) as HTMLElement;
        prevButton?.focus();
        break;
        
      case 'Home':
        event.preventDefault();
        const firstButton = document.querySelector(`[data-testid="choice-${sceneIndex}-1"]`) as HTMLElement;
        firstButton?.focus();
        break;
        
      case 'End':
        event.preventDefault();
        const lastButton = document.querySelector(`[data-testid="choice-${sceneIndex}-${choices.length}"]`) as HTMLElement;
        lastButton?.focus();
        break;
        
      case 'Escape':
        event.preventDefault();
        // フォーカスを親要素に移動（またはページの他の要素に）
        currentTarget.blur();
        break;
        
      default:
        // 数字キー（1-4）による選択
        const numKey = parseInt(event.key);
        if (numKey >= 1 && numKey <= choices.length) {
          event.preventDefault();
          const targetChoice = choices[numKey - 1];
          onChoiceSelect(targetChoice.id);
        }
        break;
    }
  }, [disabled, onChoiceSelect, choices, sceneIndex]);

  const getChoiceTestId = (choice: Choice, index: number) => {
    return `choice-${sceneIndex}-${index + 1}`;
  };

  const getChoiceStyles = (choiceId: string) => {
    const isSelected = selectedChoiceId === choiceId;
    const isHovered = hoveredChoice === choiceId;
    
    return {
      backgroundColor: isSelected 
        ? `${currentTheme.primary}15` 
        : isHovered && !disabled
          ? `${currentTheme.surface}80`
          : 'transparent',
      borderColor: isSelected 
        ? currentTheme.primary 
        : isHovered && !disabled
          ? `${currentTheme.primary}50`
          : currentTheme.border,
      color: disabled 
        ? currentTheme.text.muted
        : currentTheme.text.primary,
      transform: isSelected && !disabled ? 'scale(1.02)' : 'scale(1)',
      boxShadow: isSelected && !disabled 
        ? `0 4px 12px ${currentTheme.primary}20`
        : isHovered && !disabled
          ? `0 2px 8px ${currentTheme.border}40`
          : 'none'
    };
  };

  const getRadioButtonStyles = (choiceId: string) => {
    const isSelected = selectedChoiceId === choiceId;
    
    return {
      borderColor: isSelected 
        ? currentTheme.primary 
        : currentTheme.border,
      backgroundColor: isSelected 
        ? currentTheme.primary 
        : 'transparent'
    };
  };

  if (!choices || choices.length === 0) {
    return (
      <div className="choice-options-empty text-center py-8" data-testid="no-choices">
        <p className="text-gray-500">選択肢がありません</p>
      </div>
    );
  }

  return (
    <div className={`choice-options ${className}`} data-testid="choice-options">
      <div className="grid gap-4">
        {choices.map((choice, index) => {
          const isSelected = selectedChoiceId === choice.id;
          const testId = getChoiceTestId(choice, index);
          
          return (
            <div
              key={choice.id}
              className={`choice-option-wrapper ${isSelected ? 'selected' : ''}`}
              data-testid={`${testId}-wrapper`}
            >
              <button
                onClick={() => handleChoiceClick(choice.id)}
                onKeyDown={(e) => handleKeyDown(e, choice.id, index)}
                onMouseEnter={() => !disabled && setHoveredChoice(choice.id)}
                onMouseLeave={() => setHoveredChoice(null)}
                onFocus={() => !disabled && setHoveredChoice(choice.id)}
                onBlur={() => setHoveredChoice(null)}
                disabled={disabled}
                className={`choice-button w-full p-4 rounded-lg border-2 transition-all duration-200 text-left
                  ${disabled 
                    ? 'cursor-not-allowed opacity-50' 
                    : 'cursor-pointer hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50'
                  }
                `}
                style={getChoiceStyles(choice.id)}
                data-testid={testId}
                data-choice-id={choice.id}
                data-selected={isSelected}
                aria-pressed={isSelected}
                aria-describedby={`${testId}-description`}
                role="radio"
                tabIndex={disabled ? -1 : 0}
              >
                <div className="flex items-start">
                  {/* Radio Button */}
                  <div className="flex-shrink-0 mr-3 mt-1">
                    <div 
                      className="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200"
                      style={getRadioButtonStyles(choice.id)}
                      aria-hidden="true"
                    >
                      {isSelected && (
                        <div 
                          className="w-2.5 h-2.5 rounded-full transition-all duration-200"
                          style={{ backgroundColor: 'white' }}
                        />
                      )}
                    </div>
                  </div>
                  
                  {/* Choice Content */}
                  <div className="flex-1 min-w-0">
                    <div className="choice-text">
                      <p className="font-medium leading-relaxed break-words">
                        {choice.text}
                      </p>
                    </div>
                    
                    {/* Hidden description for screen readers */}
                    <div 
                      id={`${testId}-description`}
                      className="sr-only"
                    >
                      選択肢{index + 1}: {choice.text}
                      {isSelected ? ' (選択済み)' : ''}
                    </div>
                  </div>
                  
                  {/* Selection Indicator */}
                  {isSelected && (
                    <div className="flex-shrink-0 ml-3">
                      <div 
                        className="w-6 h-6 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: currentTheme.primary }}
                        aria-hidden="true"
                      >
                        <svg 
                          className="w-4 h-4 text-white" 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M5 13l4 4L19 7" 
                          />
                        </svg>
                      </div>
                    </div>
                  )}
                </div>
              </button>
            </div>
          );
        })}
      </div>
      
      {/* Instructions */}
      <div className="choice-instructions mt-4 text-center">
        <p className="text-sm" style={{ color: currentTheme.text.muted }}>
          {selectedChoiceId 
            ? '選択を変更するには、他の選択肢をクリックしてください' 
            : 'ひとつの選択肢を選んでください'
          }
        </p>
      </div>
      
      {/* Hidden live region for screen readers */}
      <div 
        className="sr-only" 
        role="status" 
        aria-live="polite" 
        data-testid="choice-status"
      >
        {selectedChoiceId && (
          `選択肢が選ばれました: ${choices.find(c => c.id === selectedChoiceId)?.text}`
        )}
      </div>
    </div>
  );
};

// Utility function to validate choice data
export const validateChoices = (choices: Choice[], sceneIndex: number): boolean => {
  if (!choices || choices.length === 0) return false;
  if (choices.length !== 4) return false; // NightLoom requires exactly 4 choices
  
  return choices.every((choice, index) => {
    // Validate choice structure
    if (!choice.id || !choice.text || !choice.weights) return false;
    
    // Validate choice ID format
    const expectedId = `choice_${sceneIndex}_${index + 1}`;
    if (choice.id !== expectedId) return false;
    
    // Validate weights
    if (typeof choice.weights !== 'object') return false;
    
    return true;
  });
};

// Utility function to get choice by ID
export const getChoiceById = (choices: Choice[], choiceId: string): Choice | null => {
  return choices.find(choice => choice.id === choiceId) || null;
};

// Utility function to get choice index
export const getChoiceIndex = (choices: Choice[], choiceId: string): number => {
  return choices.findIndex(choice => choice.id === choiceId);
};

export default ChoiceOptions;

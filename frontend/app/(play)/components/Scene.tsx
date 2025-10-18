/**
 * Scene component for displaying diagnosis scenarios
 * Handles scene narrative, choices, and user interaction
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from '../../state/SessionContext';
import { useTheme } from '../../theme/ThemeProvider';

interface Choice {
  id: string;
  text: string;
  weights: Record<string, number>;
}

interface SceneData {
  sceneIndex: number;
  themeId: string;
  narrative: string;
  choices: Choice[];
}

interface SceneProps {
  sessionId: string;
  sceneIndex: number;
  onChoiceSubmit?: (choiceId: string) => void;
  onSceneComplete?: (nextSceneIndex?: number) => void;
}

export const Scene: React.FC<SceneProps> = ({
  sessionId,
  sceneIndex,
  onChoiceSubmit,
  onSceneComplete
}) => {
  const [sceneData, setSceneData] = useState<SceneData | null>(null);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { state, dispatch } = useSession();
  const { themeId } = useTheme();

  const loadScene = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/sessions/${sessionId}/scenes/${sceneIndex}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to load scene');
      }
      
      const data = await response.json();
      setSceneData(data.scene);
      
      // Update session context with current scene (using dispatch if needed)
      // This would be handled by the parent component or session actions
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, sceneIndex]);

  // Load scene data on mount or when scene index changes
  useEffect(() => {
    loadScene();
  }, [loadScene]);

  const handleChoiceSelect = (choiceId: string) => {
    setSelectedChoice(choiceId);
  };

  const handleChoiceSubmit = async () => {
    if (!selectedChoice || isSubmitting) return;
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/sessions/${sessionId}/scenes/${sceneIndex}/choice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          choiceId: selectedChoice
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to submit choice');
      }
      
      const result = await response.json();
      
      // Notify parent components
      onChoiceSubmit?.(selectedChoice);
      
      // Handle scene completion
      if (result.nextScene) {
        onSceneComplete?.(result.nextScene.sceneIndex);
      } else {
        // All scenes completed
        onSceneComplete?.();
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit choice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    loadScene();
  };

  // Loading state
  if (isLoading) {
    return (
      <div 
        className="scene-container flex items-center justify-center min-h-96 p-6"
        data-testid="loading-indicator"
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current mb-4 mx-auto"></div>
          <p className="text-lg">シーンを読み込み中...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div 
        className="scene-container flex items-center justify-center min-h-96 p-6"
        data-testid="error-container"
      >
        <div className="text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">エラーが発生しました</h2>
          <p className="text-gray-600 mb-4" data-testid="error-message">
            {error.includes('ネットワーク') || error.includes('Network') 
              ? 'ネットワークエラーが発生しました。接続を確認してください。'
              : error
            }
          </p>
          <button
            onClick={handleRetry}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            data-testid="retry-button"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  // No scene data
  if (!sceneData) {
    return (
      <div 
        className="scene-container flex items-center justify-center min-h-96 p-6"
        data-testid="error-container"
      >
        <div className="text-center">
          <p className="text-lg" data-testid="error-message">
            シーンデータが見つかりません
          </p>
          <button
            onClick={handleRetry}
            className="mt-4 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            data-testid="retry-button"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`scene-container max-w-4xl mx-auto p-6 theme-${themeId}`}
      data-testid="scene-container"
    >
      {/* Scene Header */}
      <div className="scene-header mb-8 text-center">
        <div className="text-sm text-gray-500 mb-2" data-testid="scene-counter">
          シーン {sceneIndex}
        </div>
        <div className="hidden" data-testid="scene-index">
          {sceneIndex}
        </div>
      </div>

      {/* Scene Narrative */}
      <div className="scene-narrative mb-8">
        <div
          className="bg-surface rounded-xl p-6 shadow-sm border border-border"
        >
          <p 
            className="text-lg leading-relaxed"
            data-testid="scene-narrative"
          >
            {sceneData.narrative}
          </p>
        </div>
      </div>

      {/* Choices */}
      <div className="choices-section mb-8" data-testid="choices">
        <h3 className="text-lg font-semibold mb-4 text-center">
          どの行動を選択しますか？
        </h3>
        <div className="grid gap-4">
          {sceneData.choices.map((choice, index) => (
            <button
              key={choice.id}
              onClick={() => handleChoiceSelect(choice.id)}
              className={`choice-button p-4 rounded-lg border-2 transition-all duration-200 text-left
                ${selectedChoice === choice.id
                  ? 'border-primary bg-primary/10 shadow-md scale-[1.02]'
                  : 'border-border hover:border-primary/50 hover:bg-surface/50'
                }
              `}
              data-testid={`choice-${sceneIndex}-${index + 1}`}
              disabled={isSubmitting}
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 mr-3 mt-1">
                  <div 
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center
                      ${selectedChoice === choice.id 
                        ? 'border-primary bg-primary' 
                        : 'border-gray-300'
                      }
                    `}
                  >
                    {selectedChoice === choice.id && (
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    )}
                  </div>
                </div>
                <div className="flex-1">
                  <p className="font-medium">{choice.text}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <div className="submit-section text-center">
        <button
          onClick={handleChoiceSubmit}
          disabled={!selectedChoice || isSubmitting}
          className={`px-8 py-3 rounded-lg font-semibold transition-all duration-200
            ${!selectedChoice || isSubmitting
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-primary text-white hover:bg-primary-dark shadow-md hover:shadow-lg'
            }
          `}
          data-testid="continue-button"
        >
          {isSubmitting ? (
            <>
              <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              送信中...
            </>
          ) : (
            '選択を確定'
          )}
        </button>
      </div>
    </div>
  );
};

export default Scene;

/**
 * Scene API service for NightLoom diagnosis flow
 * Handles communication with scene-related endpoints
 */

import { SessionApiError, handleApiError } from './session-api';

export interface Choice {
  id: string;
  text: string;
  weights: Record<string, number>;
}

export interface Scene {
  sceneIndex: number;
  themeId: string;
  narrative: string;
  choices: Choice[];
}

export interface SceneResponse {
  sessionId: string;
  scene: Scene;
  fallbackUsed?: boolean;
}

export interface ChoiceSubmissionRequest {
  choiceId: string;
}

export interface ChoiceSubmissionResponse {
  sessionId: string;
  nextScene?: Scene | null;
  sceneCompleted: boolean;
}

export interface SceneProgressResponse {
  sessionId: string;
  state: string;
  completedScenes: number;
  totalScenes: number;
  currentScene: number;
  progressPercentage: number;
  canProceedToResult: boolean;
  selectedKeyword?: string;
  themeId?: string;
}

export interface SceneValidationResponse {
  sessionId: string;
  sceneIndex: number;
  accessible: boolean;
  currentState: string;
  completedScenes: number;
}

export class SceneApiService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Retrieve scene data for a specific session and scene index
   */
  async getScene(sessionId: string, sceneIndex: number): Promise<SceneResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw await handleApiError(response);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof SessionApiError) {
        throw error;
      }
      throw new SessionApiError(
        'NETWORK_ERROR',
        'Failed to retrieve scene data',
        { sessionId, sceneIndex, originalError: error }
      );
    }
  }

  /**
   * Submit user choice for a scene
   */
  async submitChoice(
    sessionId: string, 
    sceneIndex: number, 
    choiceId: string
  ): Promise<ChoiceSubmissionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}/choice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ choiceId }),
      });

      if (!response.ok) {
        throw await handleApiError(response);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof SessionApiError) {
        throw error;
      }
      throw new SessionApiError(
        'NETWORK_ERROR',
        'Failed to submit choice',
        { sessionId, sceneIndex, choiceId, originalError: error }
      );
    }
  }

  /**
   * Get current session progress
   */
  async getProgress(sessionId: string): Promise<SceneProgressResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/progress`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw await handleApiError(response);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof SessionApiError) {
        throw error;
      }
      throw new SessionApiError(
        'NETWORK_ERROR',
        'Failed to retrieve progress',
        { sessionId, originalError: error }
      );
    }
  }

  /**
   * Validate scene access without retrieving data
   */
  async validateSceneAccess(sessionId: string, sceneIndex: number): Promise<SceneValidationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}/validate`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw await handleApiError(response);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof SessionApiError) {
        throw error;
      }
      throw new SessionApiError(
        'NETWORK_ERROR',
        'Failed to validate scene access',
        { sessionId, sceneIndex, originalError: error }
      );
    }
  }

  /**
   * Validate choice without submitting
   */
  async validateChoice(
    sessionId: string, 
    sceneIndex: number, 
    choiceId: string
  ): Promise<{ valid: boolean; formatValid: boolean; choiceExists: boolean }> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}/choice/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ choiceId }),
      });

      if (!response.ok) {
        throw await handleApiError(response);
      }

      const data = await response.json();
      return {
        valid: data.valid,
        formatValid: data.formatValid,
        choiceExists: data.choiceExists,
      };
    } catch (error) {
      if (error instanceof SessionApiError) {
        throw error;
      }
      throw new SessionApiError(
        'NETWORK_ERROR',
        'Failed to validate choice',
        { sessionId, sceneIndex, choiceId, originalError: error }
      );
    }
  }
}

// Default service instance
export const sceneApiService = new SceneApiService();

// Utility functions

/**
 * Extract scene number from choice ID
 */
export function getSceneFromChoiceId(choiceId: string): number | null {
  const match = choiceId.match(/^choice_(\d+)_\d+$/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Extract choice number from choice ID
 */
export function getChoiceFromChoiceId(choiceId: string): number | null {
  const match = choiceId.match(/^choice_\d+_(\d+)$/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Validate choice ID format
 */
export function isValidChoiceId(choiceId: string, expectedScene?: number): boolean {
  const sceneNum = getSceneFromChoiceId(choiceId);
  const choiceNum = getChoiceFromChoiceId(choiceId);
  
  if (sceneNum === null || choiceNum === null) return false;
  if (sceneNum < 1 || sceneNum > 4) return false;
  if (choiceNum < 1 || choiceNum > 4) return false;
  
  if (expectedScene !== undefined && sceneNum !== expectedScene) return false;
  
  return true;
}

/**
 * Generate expected choice ID
 */
export function generateChoiceId(sceneIndex: number, choiceIndex: number): string {
  return `choice_${sceneIndex}_${choiceIndex}`;
}

/**
 * Parse progress percentage from scene data
 */
export function calculateProgressPercentage(completedScenes: number, totalScenes: number = 4): number {
  return Math.min(100, Math.round((completedScenes / totalScenes) * 100));
}

/**
 * Determine if user can proceed to results
 */
export function canProceedToResult(completedScenes: number, totalScenes: number = 4): boolean {
  return completedScenes >= totalScenes;
}

/**
 * Get next scene index
 */
export function getNextSceneIndex(currentScene: number, totalScenes: number = 4): number | null {
  const nextScene = currentScene + 1;
  return nextScene <= totalScenes ? nextScene : null;
}

/**
 * Format scene display text
 */
export function formatSceneText(sceneIndex: number, totalScenes: number = 4): string {
  return `シーン ${sceneIndex} / ${totalScenes}`;
}

/**
 * Format progress text
 */
export function formatProgressText(completedScenes: number, totalScenes: number = 4): string {
  return `${completedScenes} / ${totalScenes} 完了`;
}

// Error handling utilities specific to scene operations

export function isSceneNotFoundError(error: unknown): boolean {
  return error instanceof SessionApiError && 
         (error.code === 'SESSION_NOT_FOUND' || error.message.includes('Scene') && error.message.includes('not found'));
}

export function isInvalidSceneError(error: unknown): boolean {
  return error instanceof SessionApiError && 
         (error.code === 'INVALID_SCENE_INDEX' || error.code === 'BAD_REQUEST');
}

export function isChoiceValidationError(error: unknown): boolean {
  return error instanceof SessionApiError && 
         error.code === 'VALIDATION_ERROR';
}

export function isServiceUnavailableError(error: unknown): boolean {
  return error instanceof SessionApiError && 
         error.code === 'LLM_SERVICE_UNAVAILABLE';
}

/**
 * Get user-friendly error message for scene operations
 */
export function getSceneErrorMessage(error: unknown): string {
  if (isSceneNotFoundError(error)) {
    return 'セッションまたはシーンが見つかりません。最初からやり直してください。';
  }
  
  if (isInvalidSceneError(error)) {
    return 'このシーンにはアクセスできません。前のシーンを完了してください。';
  }
  
  if (isChoiceValidationError(error)) {
    return '選択肢が無効です。有効な選択肢を選んでください。';
  }
  
  if (isServiceUnavailableError(error)) {
    return 'サービスが一時的に利用できません。しばらく待ってから再試行してください。';
  }
  
  if (error instanceof SessionApiError) {
    return error.message;
  }
  
  return 'エラーが発生しました。再試行してください。';
}

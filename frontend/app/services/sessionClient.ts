/**
 * Session API client for NightLoom MVP frontend.
 * 
 * Provides TypeScript client for session management, scene progression,
 * and result retrieval with proper error handling and type safety.
 */

import { Session, Scene, AxisScore, TypeProfile } from '../types/session';

export interface BootstrapResponse {
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

export interface SceneResponse {
  sessionId: string;
  scene: Scene;
  fallbackUsed?: boolean;
}

export interface ChoiceResponse {
  sessionId: string;
  nextScene?: Scene | null;
  sceneCompleted: boolean;
}

export interface ResultResponse {
  sessionId: string;
  keyword: string;
  axes: AxisScore[];
  type: {
    dominantAxes: string[];
    profiles: TypeProfile[];
    fallbackUsed?: boolean;
  };
  completedAt: string;
  fallbackFlags: string[];
}

export class SessionAPIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'SessionAPIError';
  }
}

export class SessionClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /**
   * Start a new diagnosis session
   */
  async bootstrap(): Promise<BootstrapResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new SessionAPIError(
          `Bootstrap failed: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SessionAPIError) {
        throw error;
      }
      throw new SessionAPIError(
        `Network error during bootstrap: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Confirm keyword selection and get first scene
   */
  async confirmKeyword(
    sessionId: string,
    keyword: string,
    source: 'suggestion' | 'manual'
  ): Promise<SceneResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/keyword`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keyword, source }),
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
        }
        if (response.status === 400) {
          throw new SessionAPIError('Invalid keyword', 400, 'INVALID_KEYWORD');
        }
        throw new SessionAPIError(
          `Keyword confirmation failed: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SessionAPIError) {
        throw error;
      }
      throw new SessionAPIError(
        `Network error during keyword confirmation: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Get scene by index (1-4)
   */
  async getScene(sessionId: string, sceneIndex: number): Promise<SceneResponse> {
    try {
      const response = await fetch(
        `${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
        }
        if (response.status === 400) {
          throw new SessionAPIError('Invalid scene access', 400, 'INVALID_SCENE_ACCESS');
        }
        throw new SessionAPIError(
          `Scene retrieval failed: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SessionAPIError) {
        throw error;
      }
      throw new SessionAPIError(
        `Network error during scene retrieval: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Submit choice for a scene
   */
  async submitChoice(
    sessionId: string,
    sceneIndex: number,
    choiceId: string
  ): Promise<ChoiceResponse> {
    try {
      const response = await fetch(
        `${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}/choice`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ choiceId }),
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
        }
        if (response.status === 400) {
          throw new SessionAPIError('Invalid choice', 400, 'INVALID_CHOICE');
        }
        throw new SessionAPIError(
          `Choice submission failed: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SessionAPIError) {
        throw error;
      }
      throw new SessionAPIError(
        `Network error during choice submission: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Get final result after completing all scenes
   */
  async getResult(sessionId: string): Promise<ResultResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/result`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new SessionAPIError('Session not found', 404, 'SESSION_NOT_FOUND');
        }
        if (response.status === 400) {
          throw new SessionAPIError('Session not completed', 400, 'SESSION_NOT_COMPLETED');
        }
        throw new SessionAPIError(
          `Result retrieval failed: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SessionAPIError) {
        throw error;
      }
      throw new SessionAPIError(
        `Network error during result retrieval: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }
}

// Default client instance
export const sessionClient = new SessionClient();

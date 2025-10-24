/**
 * Session API client for NightLoom MVP frontend.
 * 
 * Provides TypeScript client for session management, scene progression,
 * and result retrieval with proper error handling and type safety.
 */

import { Session, Scene } from '../types/session';
import type { ResultData } from '@/types/result';
import { performanceService } from './performance';

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

export type ResultResponse = ResultData;

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
  private defaultTimeout: number = 60000; // 60 seconds for dynamic generation

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /**
   * Create fetch with timeout and AbortController
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number = this.defaultTimeout
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new SessionAPIError(
          `Request timed out after ${timeout}ms. This may be due to dynamic content generation.`,
          408,
          'REQUEST_TIMEOUT'
        );
      }
      throw error;
    }
  }

  /**
   * Start a new diagnosis session
   */
  async bootstrap(): Promise<BootstrapResponse> {
    const startTime = performance.now();
    
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/sessions/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }, 30000); // Bootstrap should be faster

      const metrics = performanceService.trackApiCall(
        '/sessions/start',
        'POST',
        startTime,
        response.status
      );

      if (!response.ok) {
        throw new SessionAPIError(
          `Bootstrap failed: ${response.statusText}`,
          response.status
        );
      }

      const result = await response.json();
      
      // Record successful bootstrap timing
      performanceService.recordMetric('bootstrap', metrics.duration, true, {
        sessionId: result.sessionId,
        fallbackUsed: result.fallbackUsed
      });

      return result;
    } catch (error) {
      performanceService.trackApiCall(
        '/sessions/start',
        'POST',
        startTime,
        0
      );
      
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
    const startTime = performance.now();
    
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/sessions/${sessionId}/keyword`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keyword, source }),
      }, 60000); // Extended timeout for dynamic axis + scene generation

      performanceService.trackApiCall(
        `/sessions/${sessionId}/keyword`,
        'POST',
        startTime,
        response.status
      );

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
      performanceService.trackApiCall(
        `/sessions/${sessionId}/keyword`,
        'POST',
        startTime,
        0
      );
      
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
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        },
        45000 // Scene generation timeout
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
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/sessions/${sessionId}/scenes/${sceneIndex}/choice`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ choiceId }),
        },
        30000 // Choice submission should be fast
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
    const startTime = performance.now();
    
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/sessions/${sessionId}/result`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }, 60000); // Result generation may include AI analysis

      const metrics = performanceService.trackApiCall(
        `/sessions/${sessionId}/result`,
        'POST',
        startTime,
        response.status
      );

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

      const result = await response.json();
      
      // Record result generation performance
      performanceService.recordMetric('result_calculation', metrics.duration, true, {
        sessionId,
        axisCount: result.axes?.length || 0,
        profileCount: result.type?.profiles?.length || 0,
        fallbackUsed: result.fallbackFlags?.length > 0
      });

      return result;
    } catch (error) {
      performanceService.trackApiCall(
        `/sessions/${sessionId}/result`,
        'POST',
        startTime,
        0
      );
      
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

/**
 * React session context and reducer for NightLoom MVP.
 * 
 * Manages session state throughout the diagnosis flow with type-safe
 * state transitions and error handling.
 */

'use client';

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { Session, Scene, AxisScore, TypeProfile } from '../types/session';

// Session context state interface
export interface SessionContextState {
  // Current session data
  session: Session | null;
  currentScene: Scene | null;
  currentSceneIndex: number;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Progress tracking
  completedScenes: number[];
  canProceedToResult: boolean;
  
  // Result data
  result: {
    axes: AxisScore[];
    typeProfiles: TypeProfile[];
    completedAt?: string;
  } | null;
}

// Action types
export type SessionAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'BOOTSTRAP_SUCCESS'; payload: { session: Session } }
  | { type: 'KEYWORD_CONFIRMED'; payload: { keyword: string; firstScene: Scene } }
  | { type: 'LOAD_SCENE'; payload: { scene: Scene; sceneIndex: number } }
  | { type: 'CHOICE_SUBMITTED'; payload: { sceneIndex: number; choiceId: string; nextScene?: Scene } }
  | { type: 'RESULT_GENERATED'; payload: { axes: AxisScore[]; typeProfiles: TypeProfile[]; completedAt: string } }
  | { type: 'RESET_SESSION' };

// Initial state
const initialState: SessionContextState = {
  session: null,
  currentScene: null,
  currentSceneIndex: 0,
  isLoading: false,
  error: null,
  completedScenes: [],
  canProceedToResult: false,
  result: null,
};

// Session reducer
function sessionReducer(state: SessionContextState, action: SessionAction): SessionContextState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case 'BOOTSTRAP_SUCCESS':
      return {
        ...state,
        session: action.payload.session,
        isLoading: false,
        error: null,
      };

    case 'KEYWORD_CONFIRMED':
      if (!state.session) return state;
      
      return {
        ...state,
        session: {
          ...state.session,
          selectedKeyword: action.payload.keyword,
          state: 'PLAY',
        },
        currentScene: action.payload.firstScene,
        currentSceneIndex: 1,
        isLoading: false,
        error: null,
      };

    case 'LOAD_SCENE':
      return {
        ...state,
        currentScene: action.payload.scene,
        currentSceneIndex: action.payload.sceneIndex,
        isLoading: false,
        error: null,
      };

    case 'CHOICE_SUBMITTED':
      const newCompletedScenes = [...state.completedScenes];
      if (!newCompletedScenes.includes(action.payload.sceneIndex)) {
        newCompletedScenes.push(action.payload.sceneIndex);
      }
      
      const allScenesCompleted = newCompletedScenes.length === 4;
      
      return {
        ...state,
        completedScenes: newCompletedScenes,
        canProceedToResult: allScenesCompleted,
        currentScene: action.payload.nextScene || null,
        currentSceneIndex: action.payload.nextScene ? action.payload.nextScene.sceneIndex : state.currentSceneIndex,
        isLoading: false,
        error: null,
      };

    case 'RESULT_GENERATED':
      return {
        ...state,
        result: {
          axes: action.payload.axes,
          typeProfiles: action.payload.typeProfiles,
          completedAt: action.payload.completedAt,
        },
        session: state.session ? {
          ...state.session,
          state: 'RESULT',
          completedAt: action.payload.completedAt,
        } : null,
        isLoading: false,
        error: null,
      };

    case 'RESET_SESSION':
      return initialState;

    default:
      return state;
  }
}

// Context creation
const SessionContext = createContext<{
  state: SessionContextState;
  dispatch: React.Dispatch<SessionAction>;
} | null>(null);

// Provider component
interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  return (
    <SessionContext.Provider value={{ state, dispatch }}>
      {children}
    </SessionContext.Provider>
  );
}

// Custom hook for using session context
export function useSession() {
  const context = useContext(SessionContext);
  
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  
  return context;
}

// Action creators for common operations
export const sessionActions = {
  setLoading: (loading: boolean): SessionAction => ({
    type: 'SET_LOADING',
    payload: loading,
  }),

  setError: (error: string | null): SessionAction => ({
    type: 'SET_ERROR',
    payload: error,
  }),

  bootstrapSuccess: (session: Session): SessionAction => ({
    type: 'BOOTSTRAP_SUCCESS',
    payload: { session },
  }),

  keywordConfirmed: (keyword: string, firstScene: Scene): SessionAction => ({
    type: 'KEYWORD_CONFIRMED',
    payload: { keyword, firstScene },
  }),

  loadScene: (scene: Scene, sceneIndex: number): SessionAction => ({
    type: 'LOAD_SCENE',
    payload: { scene, sceneIndex },
  }),

  choiceSubmitted: (sceneIndex: number, choiceId: string, nextScene?: Scene): SessionAction => ({
    type: 'CHOICE_SUBMITTED',
    payload: { sceneIndex, choiceId, nextScene },
  }),

  resultGenerated: (axes: AxisScore[], typeProfiles: TypeProfile[], completedAt: string): SessionAction => ({
    type: 'RESULT_GENERATED',
    payload: { axes, typeProfiles, completedAt },
  }),

  resetSession: (): SessionAction => ({
    type: 'RESET_SESSION',
  }),
};

// Selector hooks for common state derivations
export function useSessionId(): string | null {
  const { state } = useSession();
  return state.session?.id || null;
}

export function useCurrentScene(): Scene | null {
  const { state } = useSession();
  return state.currentScene;
}

export function useSessionProgress(): {
  completedScenes: number;
  totalScenes: number;
  progressPercentage: number;
  canProceedToResult: boolean;
} {
  const { state } = useSession();
  
  const completedScenes = state.completedScenes.length;
  const totalScenes = 4;
  const progressPercentage = (completedScenes / totalScenes) * 100;
  
  return {
    completedScenes,
    totalScenes,
    progressPercentage,
    canProceedToResult: state.canProceedToResult,
  };
}

export function useSessionResult(): {
  axes: AxisScore[];
  typeProfiles: TypeProfile[];
  completedAt?: string;
} | null {
  const { state } = useSession();
  return state.result;
}

export function useSessionTheme(): string {
  const { state } = useSession();
  return state.session?.themeId || 'fallback';
}

// Validation helpers
export function validateSessionState(state: SessionContextState): string[] {
  const errors: string[] = [];
  
  if (state.session && state.session.state === 'PLAY') {
    if (!state.session.selectedKeyword) {
      errors.push('Selected keyword is required in PLAY state');
    }
    
    if (state.completedScenes.length > 4) {
      errors.push('Cannot have more than 4 completed scenes');
    }
  }
  
  if (state.session && state.session.state === 'RESULT') {
    if (!state.result) {
      errors.push('Result data is required in RESULT state');
    }
  }
  
  return errors;
}

/**
 * TypeScript type definitions for NightLoom session models.
 * 
 * Mirrors the Pydantic models from backend/app/models/session.py
 * to ensure type safety across frontend-backend communication.
 */

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

export interface ChoiceRecord {
  sceneIndex: number;
  choiceId: string;
  timestamp: string;
}

export interface Axis {
  id: string;
  name: string;
  description: string;
  direction: string;
}

export interface AxisScore {
  axisId: string;
  score: number;
  rawScore: number;
}

export interface TypeProfile {
  name: string;
  description: string;
  keywords?: string[];
  dominantAxes: string[];
  polarity: string;
  meta?: Record<string, any>;
}

export interface ThemeDescriptor {
  themeId: string;
  palette: Record<string, any>;
  typography: Record<string, any>;
  assets: string[];
}

export type SessionState = 'INIT' | 'PLAY' | 'RESULT';

export interface Session {
  id: string;
  state: SessionState;
  
  // Bootstrap phase
  initialCharacter: string;
  keywordCandidates: string[];
  selectedKeyword?: string;
  themeId: string;
  
  // Play phase
  scenes: Scene[];
  choices: ChoiceRecord[];
  
  // Result phase
  rawScores: Record<string, number>;
  normalizedScores: Record<string, number>;
  typeProfiles: TypeProfile[];
  fallbackFlags: string[];
  
  // Timestamps
  createdAt: string;
  completedAt?: string;
}

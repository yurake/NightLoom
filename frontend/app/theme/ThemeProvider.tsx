"use client";

import { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { adventureTokens } from "./tokens/adventure";
import { sereneTokens } from "./tokens/serene";
import { focusTokens } from "./tokens/focus";
import { fallbackTokens } from "./tokens/fallback";

export type ThemeId = "adventure" | "serene" | "focus" | "fallback";

const themeMap: Record<ThemeId, Record<string, string>> = {
  adventure: adventureTokens,
  serene: sereneTokens,
  focus: focusTokens,
  fallback: fallbackTokens,
};

type ThemePalette = {
  primary: string;
  secondary: string;
  border: string;
  background: string;
  surface: string;
  accent: string;
  text: {
    primary: string;
    secondary: string;
    muted: string;
  };
};

type ThemeContextValue = {
  themeId: ThemeId;
  setThemeId: (value: ThemeId) => void;
  currentTheme: ThemePalette;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function applyThemeTokens(themeId: ThemeId) {
  const tokens = themeMap[themeId];

  // null/undefinedチェックとフォールバック処理
  if (!tokens || typeof tokens !== 'object') {
    console.warn(`Theme tokens for "${themeId}" are not available, falling back to fallback theme`);
    const fallbackThemeTokens = themeMap.fallback;
    if (!fallbackThemeTokens || typeof fallbackThemeTokens !== 'object') {
      console.error('Fallback theme tokens are not available');
      return;
    }
    
    Object.entries(fallbackThemeTokens).forEach(([key, value]) => {
      if (typeof value === 'string') {
        const cssVar = key === "backgroundImage" ? "--background-image" : `--color-${key}`;
        document.documentElement.style.setProperty(cssVar, value);
      }
    });
    return;
  }

  Object.entries(tokens).forEach(([key, value]) => {
    if (typeof value === 'string') {
      const cssVar = key === "backgroundImage" ? "--background-image" : `--color-${key}`;
      document.documentElement.style.setProperty(cssVar, value);
    }
  });
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeId, setThemeIdInternal] = useState<ThemeId>("fallback");

  useEffect(() => {
    try {
      applyThemeTokens(themeId);
    } catch (error) {
      console.error(`Failed to apply theme "${themeId}":`, error);
      // フォールバックテーマを適用
      if (themeId !== "fallback") {
        applyThemeTokens("fallback");
      }
    }
  }, [themeId]);

  const setThemeId = useCallback((value: ThemeId) => {
    // 有効なテーマIDかチェック
    if (value && themeMap[value]) {
      setThemeIdInternal(value);
    } else {
      console.warn(`Invalid theme ID "${value}", falling back to fallback theme`);
      setThemeIdInternal("fallback");
    }
  }, []);

  const currentTheme = useMemo<ThemePalette>(() => {
    const tokens = themeMap[themeId] ?? themeMap.fallback;
    const primary = tokens.accent ?? themeMap.fallback.accent;
    const surface = tokens.surface ?? themeMap.fallback.surface;
    const textPrimary = tokens.text ?? themeMap.fallback.text;

    return {
      primary,
      accent: primary,
      secondary: `${primary}33`, // 20% opacity overlay
      border: 'rgba(255, 255, 255, 0.24)',
      background: surface,
      surface,
      text: {
        primary: textPrimary,
        secondary: 'rgba(255, 255, 255, 0.78)',
        muted: 'rgba(255, 255, 255, 0.55)',
      },
    };
  }, [themeId]);

  const contextValue = useMemo(
    () => ({ themeId, setThemeId, currentTheme }),
    [themeId, setThemeId, currentTheme]
  );

  return (
    <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}

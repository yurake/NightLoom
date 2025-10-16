"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
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

type ThemeContextValue = {
  themeId: ThemeId;
  setThemeId: (value: ThemeId) => void;
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

  const setThemeId = (value: ThemeId) => {
    // 有効なテーマIDかチェック
    if (value && themeMap[value]) {
      setThemeIdInternal(value);
    } else {
      console.warn(`Invalid theme ID "${value}", falling back to fallback theme`);
      setThemeIdInternal("fallback");
    }
  };

  const contextValue = useMemo(() => ({ themeId, setThemeId }), [themeId]);

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

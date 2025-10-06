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

  Object.entries(tokens).forEach(([key, value]) => {
    const cssVar = key === "backgroundImage" ? "--background-image" : `--color-${key}`;
    document.documentElement.style.setProperty(cssVar, value);
  });
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeId, setThemeIdInternal] = useState<ThemeId>("fallback");

  useEffect(() => {
    applyThemeTokens(themeId);
  }, [themeId]);

  const setThemeId = (value: ThemeId) => {
    setThemeIdInternal(value);
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

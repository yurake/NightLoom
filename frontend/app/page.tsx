"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "./theme/ThemeProvider";

const themes = [
  { id: "adventure", name: "Adventure", description: "冒険的なテーマ" },
  { id: "serene", name: "Serene", description: "穏やかなテーマ" },
  { id: "focus", name: "Focus", description: "集中的なテーマ" },
  { id: "fallback", name: "Fallback", description: "標準テーマ" },
];

export default function HomePage() {
  const router = useRouter();
  const { setThemeId } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);

  const handleThemeSelect = (themeId: string) => {
    setSelectedTheme(themeId);
    setThemeId(themeId as any);
  };

  const handleStartDiagnosis = () => {
    router.push('/play');
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-900 to-purple-900">
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-4xl font-bold text-white mb-8">NightLoom</h1>
        <p className="text-xl text-white/80 mb-12">診断テーマを選択してください</p>
        
        <div className="grid grid-cols-2 gap-4 mb-8">
          {themes.map((theme) => (
            <button
              key={theme.id}
              onClick={() => handleThemeSelect(theme.id)}
              className={`p-6 rounded-lg border-2 transition-all ${
                selectedTheme === theme.id
                  ? 'border-accent bg-accent/20'
                  : 'border-white/20 bg-white/10 hover:bg-white/20'
              }`}
              role="button"
              aria-pressed={selectedTheme === theme.id}
            >
              <h3 className="text-lg font-semibold text-white mb-2">{theme.name}</h3>
              <p className="text-sm text-white/70">{theme.description}</p>
            </button>
          ))}
        </div>

        <button
          onClick={handleStartDiagnosis}
          disabled={!selectedTheme}
          className="px-8 py-3 bg-accent text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
        >
          診断を開始
        </button>
      </div>
    </main>
  );
}

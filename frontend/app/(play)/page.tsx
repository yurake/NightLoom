"use client";

import Link from "next/link";
import { ThemeId, useTheme } from "../theme/ThemeProvider";

const themeOptions: { id: ThemeId; label: string }[] = [
  { id: "adventure", label: "Adventure" },
  { id: "serene", label: "Serene" },
  { id: "focus", label: "Focus" },
  { id: "fallback", label: "Fallback" },
];

export default function PlayPage() {
  const { themeId, setThemeId } = useTheme();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 p-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">NightLoom</h1>
        <p className="text-base text-white/70">
          初期プロンプトの UI プロトタイプ。テーマ切替ボタンで表示スタイルを切り替えられます。
        </p>
      </header>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur">
        <h2 className="text-xl font-medium">テーマプレビュー</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {themeOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                option.id === themeId
                  ? "bg-accent text-surface"
                  : "bg-white/10 text-white hover:bg-white/20"
              }`}
              onClick={() => setThemeId(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">次のステップ</h2>
        <ol className="list-decimal space-y-2 pl-5">
          <li>バックエンドの bootstrap API と接続し、候補語を取得する。</li>
          <li>seed word を送信し、シーン 1 のレスポンスを描画する。</li>
          <li>Playwright でテーマ切替と初回プロンプトの e2e を追加する。</li>
        </ol>
      </section>

      <footer className="mt-auto flex justify-end text-sm text-white/60">
        <Link href="/" className="hover:text-white">
          Back to top
        </Link>
      </footer>
    </main>
  );
}

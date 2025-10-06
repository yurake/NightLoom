import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "var(--color-accent)",
        surface: "var(--color-surface)",
        text: "var(--color-text)",
      },
    },
  },
  plugins: [],
};

export default config;

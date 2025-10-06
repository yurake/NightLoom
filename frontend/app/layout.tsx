import "./globals.css";
import type { Metadata } from "next";
import { ThemeProvider } from "./theme/ThemeProvider";

export const metadata: Metadata = {
  title: "NightLoom",
  description: "Interactive persona exploration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

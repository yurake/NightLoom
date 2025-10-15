import "./globals.css";
import type { Metadata } from "next";
import { ThemeProvider } from "./theme/ThemeProvider";
import { SessionProvider } from "./state/SessionContext";

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
        <SessionProvider>
          <ThemeProvider>{children}</ThemeProvider>
        </SessionProvider>
      </body>
    </html>
  );
}

import "./globals.css";
import type { Metadata } from "next";
import { ThemeProvider } from "./theme/ThemeProvider";
import { SessionProvider } from "./state/SessionContext";

export const metadata: Metadata = {
  title: "NightLoom",
  description: "Interactive persona exploration",
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
  themeColor: '#8ab4f8',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'NightLoom',
  },
  formatDetection: {
    telephone: false,
  },
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

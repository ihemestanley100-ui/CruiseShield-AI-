import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { AmbientBackground } from "../components/ambient-background";
import { AppShell } from "../components/app-shell";
import { ThemeProvider } from "../components/theme-provider";
import "./globals.css";
import "../styles/landing.css";

export const metadata: Metadata = {
  title: "CruiseShield AI™ | The Financial Crime Immune System™",
  description:
    "CruiseShield AI is an intelligence-driven financial crime investigation platform designed to connect transaction, account, device, IP, geolocation and network intelligence with explainable analysis, evidence provenance and human oversight.",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icons/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/icons/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/favicon-48x48.png", sizes: "48x48", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
    apple: [
      {
        url: "/icons/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
  openGraph: {
    title: "CruiseShield AI™ | The Financial Crime Immune System™",
    description:
      "Connect transaction, account, device, IP, geolocation and network intelligence with explainable analysis and human oversight.",
    type: "website",
    // Relative brand asset: absolute URL needs the deployment domain.
    images: [
      {
        url: "/icons/icon-512.png",
        width: 512,
        height: 512,
        alt: "CruiseShield AI shield logo",
      },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#0a1628",
};

/* Must mirror lib/theme.ts (STORAGE_KEY + resolve rules): runs before paint
 * so the saved/system theme applies with no flash. */
const THEME_INIT_SCRIPT = `(function(){try{var m=localStorage.getItem('cruiseshield-theme')||'system';var l=m==='light'||(m==='system'&&window.matchMedia('(prefers-color-scheme: light)').matches);document.documentElement.dataset.theme=l?'light':'dark';}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Script id="theme-init" strategy="beforeInteractive">
          {THEME_INIT_SCRIPT}
        </Script>
        <ThemeProvider>
          <AmbientBackground />
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}

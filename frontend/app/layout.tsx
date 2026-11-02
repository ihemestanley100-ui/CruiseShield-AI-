import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { AmbientBackground } from "../components/ambient-background";
import { AppShell } from "../components/app-shell";
import { ThemeProvider } from "../components/theme-provider";
import { LOCALE_STORAGE_KEY, RTL_BASE_LANGS } from "../lib/i18n/registry";
import { LocaleProvider } from "../lib/i18n/context";
import { resolveMetadataBase } from "../lib/site-url";
import "./globals.css";
import "../styles/landing.css";

export const metadata: Metadata = {
  // J3 closeout (frontend EV38): absolute openGraph URLs resolve against
  // NEXT_PUBLIC_SITE_URL when the owner sets it at staging; unset keeps
  // the relative brand-asset URLs below (local/demo behavior unchanged).
  metadataBase: resolveMetadataBase(),
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

/* Must mirror lib/i18n (LOCALE_STORAGE_KEY + RTL base set, both
 * interpolated below): applies the saved locale's lang/dir before
 * paint so no flash occurs. Only strict BCP 47-shaped values pass. */
const LOCALE_INIT_SCRIPT = `(function(){try{var k=${JSON.stringify(LOCALE_STORAGE_KEY)};var v=localStorage.getItem(k)||'en';if(!/^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$/.test(v)){v='en';}var rtl=${JSON.stringify(RTL_BASE_LANGS)};document.documentElement.lang=v;document.documentElement.dir=rtl.indexOf(v.split('-')[0])>=0?'rtl':'ltr';}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Script id="theme-init" strategy="beforeInteractive">
          {THEME_INIT_SCRIPT}
        </Script>
        <Script id="locale-init" strategy="beforeInteractive">
          {LOCALE_INIT_SCRIPT}
        </Script>
        <ThemeProvider>
          <LocaleProvider>
            <AmbientBackground />
            <AppShell>{children}</AppShell>
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

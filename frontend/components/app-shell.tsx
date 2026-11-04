"use client";

/* Global application shell: top bar (brand, theme, disclosure, demo
 * profile) plus sidebar navigation with mobile drawer. Every link
 * targets a real route or a real on-page anchor; destinations without
 * backend support (Transactions, Reports, Settings, New Investigation)
 * are omitted rather than faked. Seeded record IDs below are the same
 * route parameters the Command Center already links to. */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { LanguageSelector } from "./language-selector";
import { LoginCard, useDemoSession } from "./login-gate";
import { Notifications } from "./notifications";
import { SkipLink } from "./skip-link";
import { ThemeSelector } from "./theme-selector";
import { useTranslation } from "../lib/i18n/context";

const INV_ID = "inv_84721";
const TXN_ID = "txn_84721";
const CASE_ID = "case_84721";
const SCENARIO_ID = "scn_primary";

interface NavItem {
  key: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: "commandCenter", href: "/demo" },
  { key: "investigations", href: `/investigations/${INV_ID}` },
  { key: "cases", href: `/cases/${CASE_ID}` },
  { key: "networkExplorer", href: `/network/${TXN_ID}` },
  { key: "replaySimulation", href: `/replay/${SCENARIO_ID}` },
  { key: "evidence", href: `/investigations/${INV_ID}#evidence-h` },
  { key: "aiIntelligence", href: `/investigations/${INV_ID}#ai-h` },
  { key: "auditTrail", href: `/cases/${CASE_ID}/audit` },
];

const QUICK_ACTIONS: NavItem[] = [
  { key: "exploreNetwork", href: `/network/${TXN_ID}` },
  { key: "runSimulation", href: `/replay/${SCENARIO_ID}` },
  { key: "viewAuditTrail", href: `/cases/${CASE_ID}/audit` },
];

function isActive(pathname: string, href: string): boolean {
  const path = href.split("#")[0] ?? href;
  if (path === "/demo") return pathname === "/demo";
  return pathname === path || pathname.startsWith(`${path}/`);
}

/* Same immutable official asset as the landing page (static here;
 * rotation is landing-specific). Intrinsic 69x73 matches the 1219x1290
 * asset aspect exactly; CSS scales by height. */
function ShieldMark() {
  return (
    <img
      className="shield"
      src="/assets/cruiseshield-logo-original.png"
      alt="CruiseShield AI official shield logo"
      width={69}
      height={73}
      draggable={false}
    />
  );
}

/* Minimal pre-auth chrome: brand, theme, language, badge. Shared by
 * the login card and the checking state so first paint is stable. */
function GateChrome({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation("nav");
  return (
    <div className="app-shell">
      <SkipLink />
      <header className="topbar shell-topbar">
        <Link
          href="/"
          aria-label={t("home")}
          className="shell-brand"
        >
          <ShieldMark />
          <span className="shell-brand-text">
            <span className="brand">{t("brand")}</span>
            <span className="tagline">{t("tagline")}</span>
          </span>
        </Link>
        <ThemeSelector />
        <LanguageSelector compact />
        <span className="badge synthetic">{t("synthetic")}</span>
      </header>
      <div className="shell-body">
        <main className="shell-main" id="main-content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const { t } = useTranslation("nav");
  const { t: tCommon } = useTranslation("common");
  const pathname = usePathname();
  const { gate, login, logout, logoutAll } = useDemoSession();
  const menu = useRef<HTMLButtonElement | null>(null);
  const drawer = useRef<HTMLElement | null>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  /* Focus follows the drawer: into it on open, back to the menu button
   * on close. The wasOpen guard keeps initial mount focus untouched.
   * Background scroll locks while the drawer is open (mobile). */
  /* All hooks run before any early return: landing, login gate and
   * shell render different chrome from the same hook sequence, so
   * client-side navigation and login/logout never change hook count. */
  useEffect(() => {
    if (open) {
      wasOpen.current = true;
      drawer.current?.focus();
      const previous = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = previous;
      };
    } else if (wasOpen.current) {
      wasOpen.current = false;
      menu.current?.focus();
    }
    return undefined;
  }, [open ]);

  useEffect(() => {
    if (!open) return;
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open ]);

  /* The cinematic landing owns its own chrome: render it full-bleed
   * with no sidebar or topbar. It is never login-gated: the page makes
   * no data calls, matching the backend's open "/" path. All demo
   * routes keep the shell. */
  if (pathname === "/") {
    return <div className="landing-shell">{children}</div>;
  }

  /* Checking: withhold children (and their data fetches) until the
   * mode check resolves — no content flash before the login card. */
  if (gate.status === "checking") {
    return (
      <GateChrome>
        <p className="muted" role="status">
          {tCommon("loading")}
        </p>
      </GateChrome>
    );
  }

  /* Phase 5: hosted demos with login armed show the sign-in card
   * instead of any demo route until the session cookie is set. */
  if (gate.status === "login") {
    return (
      <GateChrome>
        <LoginCard onLogin={login} />
      </GateChrome>
    );
  }

  return (
    <div className="app-shell">
      <SkipLink />
      <header className="topbar shell-topbar">
        <button
          ref={menu}
          type="button"
          className="menu-btn btn-secondary btn-icon"
          aria-expanded={open}
          aria-controls="app-sidebar"
          aria-label={t("toggleNav")}
          onClick={() => setOpen(!open)}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              d="M2 5h16M2 10h16M2 15h16"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
        <Link
          href="/"
          aria-label={t("home")}
          className="shell-brand"
        >
          <ShieldMark />
          <span className="shell-brand-text">
            <span className="brand">{t("brand")}</span>
            <span className="tagline">{t("tagline")}</span>
          </span>
        </Link>
        <ThemeSelector />
        <LanguageSelector compact />
        <Notifications />
        <span className="badge synthetic">{t("synthetic")}</span>
        {gate.status === "authed" ? (
          <div className="profile">
            <span className="avatar" aria-hidden="true">
              {gate.session.user.slice(0, 2).toUpperCase()}
            </span>
            <span className="profile-text">
              <strong>{gate.session.user}</strong>
              <span className="muted">
                {t("roleDemo", { role: gate.session.role })}
              </span>
            </span>
            <button
              type="button"
              className="btn-tertiary"
              onClick={() => void logout()}
            >
              {t("signOut")}
            </button>
            <button
              type="button"
              className="btn-tertiary"
              title={t("signOutEverywhereTitle")}
              onClick={() => void logoutAll()}
            >
              {t("signOutEverywhere")}
            </button>
          </div>
        ) : (
          <div className="profile">
            <span className="avatar" aria-hidden="true">
              IN
            </span>
            <span className="profile-text">
              <strong>{t("investigator")}</strong>
              <span className="muted">{t("demoRole")}</span>
            </span>
          </div>
        )}
      </header>
      <div className="shell-body">
        <aside
          id="app-sidebar"
          ref={drawer}
          tabIndex={-1}
          className={open ? "sidebar open" : "sidebar"}
        >
          <nav aria-label={t("primary")}>
            <ul className="side-nav">
              {NAV_ITEMS.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={
                      isActive(pathname, item.href) ? "page" : undefined
                    }
                    onClick={() => setOpen(false)}
                  >
                    {t(item.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          {/* Label, not a section heading: keeps the document outline
              starting at the page h1 (a11y audit P7). */}
          <p className="side-label">{t("quickActions")}</p>
          <ul className="side-actions">
            {QUICK_ACTIONS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="action-btn"
                  onClick={() => setOpen(false)}
                >
                  {t(item.key)}
                </Link>
              </li>
            ))}
          </ul>
        </aside>
        {open && (
          <button
            type="button"
            className="side-overlay"
            aria-label={t("closeNav")}
            onClick={() => setOpen(false)}
          />
        )}
        <main className="shell-main" id="main-content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

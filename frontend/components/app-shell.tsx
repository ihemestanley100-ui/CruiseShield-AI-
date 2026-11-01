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
import { LoginCard, useDemoSession } from "./login-gate";
import { Notifications } from "./notifications";
import { ThemeSelector } from "./theme-selector";

const INV_ID = "inv_84721";
const TXN_ID = "txn_84721";
const CASE_ID = "case_84721";
const SCENARIO_ID = "scn_primary";

interface NavItem {
  label: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Command Center", href: "/demo" },
  { label: "Investigations", href: `/investigations/${INV_ID}` },
  { label: "Cases", href: `/cases/${CASE_ID}` },
  { label: "Network Explorer", href: `/network/${TXN_ID}` },
  { label: "Replay & Simulation", href: `/replay/${SCENARIO_ID}` },
  { label: "Evidence", href: `/investigations/${INV_ID}#evidence-h` },
  { label: "AI Intelligence", href: `/investigations/${INV_ID}#ai-h` },
  { label: "Audit Trail", href: `/cases/${CASE_ID}/audit` },
];

const QUICK_ACTIONS: NavItem[] = [
  { label: "Explore Network", href: `/network/${TXN_ID}` },
  { label: "Run Simulation", href: `/replay/${SCENARIO_ID}` },
  { label: "View Audit Trail", href: `/cases/${CASE_ID}/audit` },
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

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { gate, login, logout } = useDemoSession();
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

  /* Phase 5: hosted demos with login armed show the sign-in card
   * instead of any demo route until the session cookie is set. */
  if (gate.status === "login") {
    return (
      <div className="app-shell">
        <header className="topbar shell-topbar">
          <Link
            href="/"
            aria-label="CruiseShield AI home"
            className="shell-brand"
          >
            <ShieldMark />
            <span className="shell-brand-text">
              <span className="brand">CruiseShield AI</span>
              <span className="tagline">Financial Crime Immune System™</span>
            </span>
          </Link>
          <ThemeSelector />
          <span className="badge synthetic">Synthetic demo data</span>
        </header>
        <div className="shell-body">
          <div className="shell-main">
            <LoginCard onLogin={login} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar shell-topbar">
        <button
          ref={menu}
          type="button"
          className="menu-btn btn-secondary btn-icon"
          aria-expanded={open}
          aria-controls="app-sidebar"
          aria-label="Toggle navigation"
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
          aria-label="CruiseShield AI home"
          className="shell-brand"
        >
          <ShieldMark />
          <span className="shell-brand-text">
            <span className="brand">CruiseShield AI</span>
            <span className="tagline">Financial Crime Immune System™</span>
          </span>
        </Link>
        <ThemeSelector />
        <Notifications />
        <span className="badge synthetic">Synthetic demo data</span>
        {gate.status === "authed" ? (
          <div className="profile">
            <span className="avatar" aria-hidden="true">
              {gate.session.user.slice(0, 2).toUpperCase()}
            </span>
            <span className="profile-text">
              <strong>{gate.session.user}</strong>
              <span className="muted">{gate.session.role} · demo</span>
            </span>
            <button
              type="button"
              className="btn-tertiary"
              onClick={() => void logout()}
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="profile">
            <span className="avatar" aria-hidden="true">
              IN
            </span>
            <span className="profile-text">
              <strong>Investigator</strong>
              <span className="muted">demo role</span>
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
          <nav aria-label="Primary">
            <ul className="side-nav">
              {NAV_ITEMS.map((item) => (
                <li key={item.label}>
                  <Link
                    href={item.href}
                    aria-current={
                      isActive(pathname, item.href) ? "page" : undefined
                    }
                    onClick={() => setOpen(false)}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          {/* Label, not a section heading: keeps the document outline
              starting at the page h1 (a11y audit P7). */}
          <p className="side-label">Quick Actions</p>
          <ul className="side-actions">
            {QUICK_ACTIONS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="action-btn"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </aside>
        {open && (
          <button
            type="button"
            className="side-overlay"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
          />
        )}
        <div className="shell-main">{children}</div>
      </div>
    </div>
  );
}

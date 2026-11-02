"use client";

import Link from "next/link";
import { LanguageSelector } from "../language-selector";
import { useTranslation } from "../../lib/i18n/context";

/* Top navigation bar + hero headlines + primary call to action. */

/* Official immutable brand asset. Never redraw, recolour, crop, or
 * substitute this file; all presentation lives on the CSS wrapper. */
export const OFFICIAL_LOGO_SRC = "/assets/cruiseshield-logo-original.png";
export const OFFICIAL_LOGO_ALT = "CruiseShield AI official shield logo";
/* Intrinsic dimensions matching the official 1219x1290 asset aspect
 * (69/73 = 0.9452, exact). Prevents layout shift and distortion;
 * CSS scales proportionally by height only. */
const LOGO_WIDTH = 69;
const LOGO_HEIGHT = 73;

export function OfficialLogo() {
  return (
    <span className="landing-logo">
      <span className="landing-logo-spin">
        <img
          src={OFFICIAL_LOGO_SRC}
          alt={OFFICIAL_LOGO_ALT}
          width={LOGO_WIDTH}
          height={LOGO_HEIGHT}
          draggable={false}
        />
      </span>
    </span>
  );
}

export function LandingNav() {
  const { t, tl } = useTranslation("landing");
  const signals = tl("signals");
  return (
    <header className="landing-nav">
      <Link href="/" className="landing-brand" aria-label={t("home")}>
        <OfficialLogo />
        <span>
          <strong>{t("brandName")}</strong>
          <small>{t("tagline")}</small>
        </span>
      </Link>
      <nav className="landing-signals" aria-label={t("platformQualities")}>
        {signals.map((signal) => (
          <span key={signal} className="landing-signal">
            <span className="landing-signal-dot" aria-hidden="true" />
            {signal}
          </span>
        ))}
      </nav>
      <LanguageSelector compact />
      <Link href="/demo" className="landing-enter">
        {t("enterDemo")}
      </Link>
    </header>
  );
}

export function LandingHeroCopy() {
  /* Canonical investigation workflow; must match the demo's 8 stages. */
  const { t, tl } = useTranslation("landing");
  const journey = tl("journey");
  return (
    <div className="landing-hero-copy">
      <p className="landing-eyebrow">{t("eyebrow")}</p>
      <h1 id="landing-h1">{t("h1")}</h1>
      <p className="landing-sub">{t("problem")}</p>
      <p className="landing-sub">{t("beneficiaries")}</p>
      <ol className="landing-journey" aria-label={t("journeyLabel")}>
        {journey.map((step, index) => (
          <li key={step}>
            <span>{step}</span>
            {index < journey.length - 1 && (
              <span className="landing-journey-arrow" aria-hidden="true">
                →
              </span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function LandingCta({ onActivate }: { onActivate?: () => void }) {
  const { t } = useTranslation("landing");
  return (
    <div className="landing-cta-wrap">
      <Link
        href="/demo"
        className="landing-cta"
        onMouseEnter={onActivate}
        onClick={onActivate}
      >
        {t("cta")} <span aria-hidden="true">→</span>
      </Link>
      <p className="landing-cta-sub">{t("ctaSub")}</p>
    </div>
  );
}

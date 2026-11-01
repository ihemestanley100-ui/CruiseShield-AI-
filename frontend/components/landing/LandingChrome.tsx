import Link from "next/link";

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

const JOURNEY = ["DETECT", "CONNECT", "EXPLAIN", "PREVENT", "PROTECT"];

const SIGNALS = ["Secure", "Intelligent", "Global", "Always On"];

export function LandingNav() {
  return (
    <header className="landing-nav">
      <Link href="/" className="landing-brand" aria-label="CruiseShield AI home">
        <OfficialLogo />
        <span>
          <strong>CruiseShield AI™</strong>
          <small>The Financial Crime Immune System™</small>
        </span>
      </Link>
      <nav className="landing-signals" aria-label="Platform qualities">
        {SIGNALS.map((signal) => (
          <span key={signal} className="landing-signal">
            <span className="landing-signal-dot" aria-hidden="true" />
            {signal}
          </span>
        ))}
      </nav>
      <Link href="/demo" className="landing-enter">
        Enter Demo
      </Link>
    </header>
  );
}

export function LandingHeroCopy() {
  return (
    <div className="landing-hero-copy">
      <p className="landing-eyebrow">Global Financial Intelligence</p>
      <h1 id="landing-h1">A Safer Financial World</h1>
      <p className="landing-sub">
        Powered by Intelligence. Driven by Trust. Built for the Future.
      </p>
      <ol className="landing-journey" aria-label="Platform journey">
        {JOURNEY.map((step, index) => (
          <li key={step}>
            <span>{step}</span>
            {index < JOURNEY.length - 1 && (
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
  return (
    <div className="landing-cta-wrap">
      <Link
        href="/demo"
        className="landing-cta"
        onMouseEnter={onActivate}
        onClick={onActivate}
      >
        Explore CruiseShield AI™ <span aria-hidden="true">→</span>
      </Link>
      <p className="landing-cta-sub">Enter the Interactive Demo Experience</p>
    </div>
  );
}

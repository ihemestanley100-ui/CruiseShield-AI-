/* CruiseShield Intelligence Framework card. Permanent product
 * identity panel: rendered beside the hero flow, never inside the
 * WebGL canvas, never intercepting globe or control interactions.
 * Content is fixed product copy, hardcoded like the existing core
 * label — no locale files touched. */

"use client";

function NetworkIcon() {
  /* Hub-and-spoke network mark in the panel's existing inline-SVG
   * style (no icon dependency in the project). */
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    >
      <path d="M10.1 10.9L5.8 7.2M13.9 10.9l4.3-3.7M12 14.4v3.4" />
      <circle cx="12" cy="12" r="2.3" fill="currentColor" stroke="none" />
      <circle cx="4.6" cy="6.2" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="19.4" cy="6.2" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="12" cy="19.4" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IntelligenceFrameworkPanel() {
  return (
    <aside className="fw-panel" aria-labelledby="fw-panel-h">
      <div className="fw-panel-head">
        <span className="fw-mark" aria-hidden="true">
          <NetworkIcon />
        </span>
        <div>
          <p className="fw-eyebrow">Cruiseshield Intelligence Framework</p>
          <h2 id="fw-panel-h" className="fw-title">
            The Global Signal-to-Evidence Engine™
          </h2>
        </div>
      </div>
      <p className="fw-headline">
        From Disconnected Signals to Defensible Intelligence
      </p>
      <p className="fw-desc">
        Connect transaction patterns, entity relationships, risk intelligence
        and investigation evidence through one explainable intelligence
        framework, with human investigators retaining decision authority.
      </p>
      <p className="fw-statement">
        One intelligence framework. A stronger financial world.
      </p>
    </aside>
  );
}

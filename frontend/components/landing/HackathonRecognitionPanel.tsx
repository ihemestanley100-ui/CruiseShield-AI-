/* Meta Global AI Developer Hackathon recognition panel. Isolated
 * overlay: rendered beside the hero flow, never inside the WebGL
 * canvas, never intercepting globe or control interactions. Content
 * is a fixed commemorative plaque (proper nouns + date), hardcoded
 * like the existing core label — no locale files touched. Claims
 * participation only: no award implied (see PARTICIPANT tag). */

"use client";

/* Verified 2026-11-03: public repository, HTTP 200 unauthenticated,
 * README present. Single source for the panel link. */
export const HACKATHON_REPO_URL =
  "https://github.com/ihemestanley100-ui/CRUISESHIELD-AI-";

function TrophyIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      aria-hidden="true"
      className="hack-trophy"
    >
      <path
        d="M4 2h8v2.5a4 4 0 0 1-8 0V2z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path
        d="M4 3.5H2.5a1.5 1.5 0 0 0 1.6 2.6M12 3.5h1.5a1.5 1.5 0 0 1-1.6 2.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <path
        d="M8 8.5v2M6 14h4M8 10.5c-1 0-1.2 1.2-2 1.5h4c-.8-.3-1-1.5-2-1.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CodeIcon() {
  /* Source-code brackets mark (abstract; the link text + destination
   * identify GitHub explicitly). */
  return (
    <svg width="17" height="17" viewBox="0 0 16 16" aria-hidden="true">
      <path
        d="M6 4.5L2.5 8 6 11.5M10 4.5l3.5 3.5L10 11.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ExternalIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      aria-hidden="true"
      className="hack-external"
    >
      <path
        d="M5.5 2.5h6v6M11.5 2.5L6.5 7.5M11 8.5v3H3v-8h3"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function HackathonRecognitionPanel() {
  return (
    <aside className="hack-panel" aria-labelledby="hack-panel-h">
      <div className="hack-panel-head">
        <span className="hack-meta-mark" aria-hidden="true">
          ∞
        </span>
        <div>
          <p className="hack-eyebrow">Meta Hackathon Recognition</p>
          <h2 id="hack-panel-h" className="hack-title">
            Built at the Meta Global AI Developer Hackathon
          </h2>
        </div>
      </div>
      <p className="hack-sub">
        <TrophyIcon />
        <span>October 2026</span>
        <span className="hack-tag">Participant</span>
      </p>
      <a
        className="hack-source"
        href={HACKATHON_REPO_URL}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Source code — CruiseShield AI GitHub repository (opens in a new tab)"
      >
        <CodeIcon />
        <span className="hack-source-label">Source code</span>
        <ExternalIcon />
      </a>
    </aside>
  );
}

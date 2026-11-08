"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { useTranslation } from "../../lib/i18n/context";

/* Floating holographic panels: capabilities, module cards, regions.
 * All coverage language is illustrative; nothing claims live global
 * operations. */

const TXN = "txn_84721";
const INV = "inv_84721";
const CASE = "case_84721";

const INTEL_HREFS = [
  "/platform",
  `/network/${TXN}`,
  `/network/${TXN}`,
  `/investigations/${INV}`,
  `/investigations/${INV}`,
  `/network/${TXN}`,
  `/investigations/${INV}#ai-h`,
  "/platform",
  `/cases/${CASE}`,
];

function PanelIcon({ index }: { index: number }) {
  // Minimal geometric glyphs; shape varies by position only.
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      {index % 3 === 0 && (
        <circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" strokeWidth="1.6" />
      )}
      {index % 3 === 1 && (
        <rect x="3.5" y="3.5" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.6" />
      )}
      {index % 3 === 2 && (
        <path d="M9 2l7 14H2z" fill="none" stroke="currentColor" strokeWidth="1.6" />
      )}
      <circle cx="9" cy="9" r="1.6" fill="currentColor" />
    </svg>
  );
}

export function IntelligencePanel() {
  const { t, tl } = useTranslation("landing");
  const labels = tl("intelItems");
  const [open, setOpen] = useState(true);
  const bodyId = useId();
  return (
    <aside
      className="landing-panel landing-panel-left"
      aria-labelledby="landing-intel-h"
    >
      <div className="landing-panel-head">
        <h2 id="landing-intel-h">{t("intelTitle")}</h2>
        <button
          type="button"
          className="landing-panel-toggle"
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? t("collapsePanel") : t("expandPanel")}
        </button>
      </div>
      {open && (
        <div id={bodyId}>
          <ul>
            {labels.map((label, index) => (
              /* Index key: hrefs repeat across items, labels localize. */
              <li key={index}>
                <Link
                  href={INTEL_HREFS[index] ?? "/platform"}
                  className="landing-panel-link"
                >
                  <span className="landing-panel-icon">
                    <PanelIcon index={index} />
                  </span>
                  <span>{label}</span>
                  <span className="landing-status">{t("intelStatus")}</span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="landing-panel-note">{t("intelNote")}</p>
        </div>
      )}
    </aside>
  );
}

export function ModuleCards() {
  const { t, tl } = useTranslation("landing");
  const titles = tl("moduleTitles");
  return (
    <div className="landing-modules" aria-label={t("intelligenceModules")}>
      {titles.map((title, index) => {
        const lines = tl(`moduleLines.${index}`);
        return (
          <article key={title} className={`landing-module module-${index}`}>
            <h3>{title}</h3>
            <ul>
              {lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </article>
        );
      })}
      <p className="landing-modules-note">{t("modulesNote")}</p>
    </div>
  );
}

export function CoveragePanel() {
  const { t, tl } = useTranslation("landing");
  const regions = tl("regions");
  const [open, setOpen] = useState(true);
  const bodyId = useId();
  return (
    <aside
      className="landing-panel landing-panel-right"
      aria-labelledby="landing-regions-h"
    >
      <div className="landing-panel-head">
        <h2 id="landing-regions-h">{t("regionsTitle")}</h2>
        <button
          type="button"
          className="landing-panel-toggle"
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? t("collapsePanel") : t("expandPanel")}
        </button>
      </div>
      {open && (
        <div id={bodyId}>
          <p className="landing-illustrative">{t("illustrative")}</p>
          <ul>
            {regions.map((region) => (
              <li key={region}>
                <span className="landing-region-dot" aria-hidden="true" />
                <span>{region}</span>
              </li>
            ))}
          </ul>
          <p className="landing-panel-note">{t("regionsNote")}</p>
        </div>
      )}
    </aside>
  );
}

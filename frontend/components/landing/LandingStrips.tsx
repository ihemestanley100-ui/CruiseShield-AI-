"use client";

import Link from "next/link";
import { useTranslation } from "../../lib/i18n/context";

/* Capability strip (10 cards, real routes only) + global metrics. */

const TXN = "txn_84721";
const INV = "inv_84721";
const CASE = "case_84721";
const SCENARIO = "scn_primary";

const CAP_HREFS = [
  "/demo",
  `/network/${TXN}`,
  `/network/${TXN}`,
  `/investigations/${INV}`,
  `/investigations/${INV}`,
  `/network/${TXN}`,
  `/investigations/${INV}`,
  `/investigations/${INV}#ai-h`,
  "/demo",
  `/cases/${CASE}`,
];

export function CapabilityStrip() {
  const { t, tl } = useTranslation("landing");
  const titles = tl("capTitles");
  const subs = tl("capSubs");
  return (
    <section className="landing-strip" aria-labelledby="landing-cap-h">
      <h2 id="landing-cap-h">{t("capTitle")}</h2>
      <ul className="landing-cap-grid">
        {titles.map((title, index) => (
          /* Index key: titles localize, hrefs repeat. */
          <li key={index}>
            <Link href={CAP_HREFS[index] ?? "/demo"} className="landing-cap-card">
              <span className="landing-cap-index" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <strong>{title}</strong>
              <span className="landing-cap-sub">{subs[index] ?? ""}</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="landing-strip-note">
        {t("stripNote")}
        <Link href={`/replay/${SCENARIO}`}>{t("replayLink")}</Link>
      </p>
    </section>
  );
}

export function GlobalMetrics() {
  const { t, tl } = useTranslation("landing");
  const titles = tl("metricTitles");
  const subs = tl("metricSubs");
  return (
    <section className="landing-metrics" aria-labelledby="landing-metrics-h">
      <h2 id="landing-metrics-h" className="visually-hidden">
        {t("platformPrinciples")}
      </h2>
      <ul>
        {titles.map((title, index) => (
          <li key={index}>
            <strong>{title}</strong>
            <span>{subs[index] ?? ""}</span>
          </li>
        ))}
      </ul>
      <p className="landing-footer-line">{t("footerLine")}</p>
    </section>
  );
}

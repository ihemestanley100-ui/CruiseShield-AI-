import Link from "next/link";

/* Capability strip (10 cards, real routes only) + global metrics. */

const TXN = "txn_84721";
const INV = "inv_84721";
const CASE = "case_84721";
const SCENARIO = "scn_primary";

const CAPABILITIES: { title: string; sub: string; href: string }[] = [
  { title: "Transaction Monitoring", sub: "Real-Time Detection", href: "/demo" },
  { title: "Account Intelligence", sub: "Behaviour and Network", href: `/network/${TXN}` },
  { title: "Device Analytics", sub: "Device Linkage", href: `/network/${TXN}` },
  { title: "IP Intelligence", sub: "Network Signals", href: `/investigations/${INV}` },
  { title: "Geolocation Analysis", sub: "Global Context", href: `/investigations/${INV}` },
  { title: "Network Graph", sub: "Relationship Mapping", href: `/network/${TXN}` },
  { title: "Investigations", sub: "Case Management", href: `/investigations/${INV}` },
  { title: "AI Intelligence", sub: "Explainable Insights", href: `/investigations/${INV}#ai-h` },
  { title: "Risk Engine", sub: "Deterministic Scoring", href: "/demo" },
  { title: "Evidence & Audit", sub: "Full Traceability", href: `/cases/${CASE}` },
];

export function CapabilityStrip() {
  return (
    <section className="landing-strip" aria-labelledby="landing-cap-h">
      <h2 id="landing-cap-h">One platform, ten intelligence layers</h2>
      <ul className="landing-cap-grid">
        {CAPABILITIES.map((cap, index) => (
          <li key={cap.title}>
            <Link href={cap.href} className="landing-cap-card">
              <span className="landing-cap-index" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <strong>{cap.title}</strong>
              <span className="landing-cap-sub">{cap.sub}</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="landing-strip-note">
        Cards open the matching live demo screen ·{" "}
        <Link href={`/replay/${SCENARIO}`}>try replay &amp; simulation</Link>
      </p>
    </section>
  );
}

const METRICS: { title: string; sub: string }[] = [
  { title: "Global Reach", sub: "Illustrative Global Coverage" },
  { title: "Jurisdictional Context", sub: "Country and Regional Intelligence" },
  { title: "Multi-Layer", sub: "Intelligence Correlation" },
  { title: "Human Oversight", sub: "Explainable Investigation" },
];

export function GlobalMetrics() {
  return (
    <section className="landing-metrics" aria-labelledby="landing-metrics-h">
      <h2 id="landing-metrics-h" className="visually-hidden">
        Platform principles
      </h2>
      <ul>
        {METRICS.map((metric) => (
          <li key={metric.title}>
            <strong>{metric.title}</strong>
            <span>{metric.sub}</span>
          </li>
        ))}
      </ul>
      <p className="landing-footer-line">
        One Platform. A Safer Financial Future. For Everyone.
      </p>
    </section>
  );
}

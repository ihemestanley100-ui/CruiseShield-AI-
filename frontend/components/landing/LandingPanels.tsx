import Link from "next/link";

/* Floating holographic panels: capabilities, module cards, regions.
 * All coverage language is illustrative; nothing claims live global
 * operations. */

const TXN = "txn_84721";
const INV = "inv_84721";
const CASE = "case_84721";

interface PanelItem {
  label: string;
  href: string;
  status: string;
}

const INTEL_ITEMS: PanelItem[] = [
  { label: "Transaction Monitoring", href: "/demo", status: "Demo" },
  { label: "Account Intelligence", href: `/network/${TXN}`, status: "Demo" },
  { label: "Device Intelligence", href: `/network/${TXN}`, status: "Demo" },
  { label: "IP Intelligence", href: `/investigations/${INV}`, status: "Demo" },
  { label: "Geolocation Intelligence", href: `/investigations/${INV}`, status: "Demo" },
  { label: "Network Graph", href: `/network/${TXN}`, status: "Demo" },
  { label: "AI Investigation", href: `/investigations/${INV}#ai-h`, status: "Demo" },
  { label: "Risk Analysis", href: "/demo", status: "Demo" },
  { label: "Evidence and Audit", href: `/cases/${CASE}`, status: "Demo" },
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
  return (
    <aside
      className="landing-panel landing-panel-left"
      aria-labelledby="landing-intel-h"
    >
      <h2 id="landing-intel-h">Global Intelligence</h2>
      <ul>
        {INTEL_ITEMS.map((item, index) => (
          <li key={item.label}>
            <Link href={item.href} className="landing-panel-link">
              <span className="landing-panel-icon">
                <PanelIcon index={index} />
              </span>
              <span>{item.label}</span>
              <span className="landing-status">{item.status}</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="landing-panel-note">
        Demonstration capabilities · synthetic data
      </p>
    </aside>
  );
}

const MODULES: { title: string; lines: string[] }[] = [
  { title: "Satellite Intelligence", lines: ["Global Monitoring", "Cross-Border Risk"] },
  { title: "AI Analysis", lines: ["Explainable Insights", "Human Oversight"] },
  { title: "Global Network", lines: ["Regional Intelligence", "Cross-Border Relationships"] },
  { title: "Cyber Defense", lines: ["Proactive Protection", "Financial Crime Intelligence"] },
  { title: "Secure Infrastructure", lines: ["Privacy", "Governance", "Enterprise Architecture"] },
];

export function ModuleCards() {
  return (
    <div className="landing-modules" aria-label="Intelligence modules">
      {MODULES.map((module, index) => (
        <article key={module.title} className={`landing-module module-${index}`}>
          <h3>{module.title}</h3>
          <ul>
            {module.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </article>
      ))}
      <p className="landing-modules-note">
        Illustrative module concepts · capabilities vary by deployment
      </p>
    </div>
  );
}

const REGIONS = [
  "North America",
  "South America",
  "Europe",
  "Africa",
  "Middle East",
  "Asia Pacific",
  "Global Oceans",
  "Orbital Layer",
];

export function CoveragePanel() {
  return (
    <aside
      className="landing-panel landing-panel-right"
      aria-labelledby="landing-regions-h"
    >
      <h2 id="landing-regions-h">Global Intelligence Regions</h2>
      <p className="landing-illustrative">Illustrative Network View</p>
      <ul>
        {REGIONS.map((region) => (
          <li key={region}>
            <span className="landing-region-dot" aria-hidden="true" />
            <span>{region}</span>
          </li>
        ))}
      </ul>
      <p className="landing-panel-note">
        Simulated regional signals · not live monitoring
      </p>
    </aside>
  );
}

/* Feature cards: polished navigation to the real destinations. Every
 * footer is either a live backend value or a feature description —
 * never an invented metric. */

import Link from "next/link";

interface Props {
  invId: string;
  invStatus: string;
  txnId: string;
  caseId: string;
  caseStatus: string;
  scenarioId: string;
  graphCounts: { nodes: number; edges: number } | null;
  evidenceCount: number | null;
}

export function FeatureCards(props: Props) {
  const {
    invId,
    invStatus,
    txnId,
    caseId,
    caseStatus,
    scenarioId,
    graphCounts,
    evidenceCount,
  } = props;
  const cards = [
    {
      title: "Investigations",
      desc: "Scores, rules, evidence and AI analysis.",
      href: `/investigations/${invId}`,
      foot: `${invId} · ${invStatus}`,
    },
    {
      title: "Network Explorer",
      desc: "Accounts, devices, phones and merchants.",
      href: `/network/${txnId}`,
      foot:
        graphCounts === null
          ? "Graph unavailable"
          : `${graphCounts.nodes} nodes · ${graphCounts.edges} edges`,
    },
    {
      title: "Replay & Simulation",
      desc: "Recreate events and test what-if scenarios.",
      href: `/replay/${scenarioId}`,
      foot: "Deterministic replay",
    },
    {
      title: "Evidence",
      desc: "Linked evidence and provenance.",
      href: `/investigations/${invId}#evidence-h`,
      foot: evidenceCount === null ? "Unavailable" : `${evidenceCount} records`,
    },
    {
      title: "Cases",
      desc: "Case status and human decisions.",
      href: `/cases/${caseId}`,
      foot: `${caseId} · ${caseStatus}`,
    },
    {
      title: "Audit Trail",
      desc: "System and analyst activity.",
      href: `/cases/${caseId}/audit`,
      foot: "Full history",
    },
  ];
  return (
    <section aria-labelledby="feat-h" className="command-section">
      <h2 id="feat-h">Explore</h2>
      <div className="feature-grid">
        {cards.map((card) => (
          <Link key={card.title} href={card.href} className="feature-card">
            <strong>{card.title}</strong>
            <span className="feature-desc">{card.desc}</span>
            <span className="feature-foot muted">{card.foot}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

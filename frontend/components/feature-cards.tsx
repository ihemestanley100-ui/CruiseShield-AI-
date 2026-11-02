"use client";

/* Feature cards: polished navigation to the real destinations. Every
 * footer is either a live backend value or a feature description —
 * never an invented metric. */

import Link from "next/link";
import { useTranslation } from "../lib/i18n/context";

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
  const { t } = useTranslation("command");
  const cards = [
    {
      key: "inv",
      title: t("featInv"),
      desc: t("featInvDesc"),
      href: `/investigations/${invId}`,
      foot: t("caseStatusLine", { case: invId, status: invStatus }),
    },
    {
      key: "net",
      title: t("featNet"),
      desc: t("featNetDesc"),
      href: `/network/${txnId}`,
      foot:
        graphCounts === null
          ? t("featGraphDown")
          : t("featGraphFoot", {
              a: graphCounts.nodes,
              b: graphCounts.edges,
            }),
    },
    {
      key: "replay",
      title: t("featReplay"),
      desc: t("featReplayDesc"),
      href: `/replay/${scenarioId}`,
      foot: t("featReplayFoot"),
    },
    {
      key: "ev",
      title: t("featEv"),
      desc: t("featEvDesc"),
      href: `/investigations/${invId}#evidence-h`,
      foot:
        evidenceCount === null
          ? t("featEvDown")
          : t("featEvFoot", { n: evidenceCount }),
    },
    {
      key: "cases",
      title: t("featCases"),
      desc: t("featCasesDesc"),
      href: `/cases/${caseId}`,
      foot: t("caseStatusLine", { case: caseId, status: caseStatus }),
    },
    {
      key: "audit",
      title: t("featAudit"),
      desc: t("featAuditDesc"),
      href: `/cases/${caseId}/audit`,
      foot: t("featAuditFoot"),
    },
  ];
  return (
    <section aria-labelledby="feat-h" className="command-section">
      <h2 id="feat-h">{t("featTitle")}</h2>
      <div className="feature-grid">
        {cards.map((card) => (
          <Link key={card.key} href={card.href} className="feature-card">
            <strong>{card.title}</strong>
            <span className="feature-desc">{card.desc}</span>
            <span className="feature-foot muted">{card.foot}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

/* Investigation workflow strip: the judge-friendly stage path. Every
 * stage links to the real route that performs it. */

"use client";

import Link from "next/link";
import { useTranslation } from "../lib/i18n/context";

interface Props {
  invId: string;
  txnId: string;
  caseId: string;
  scenarioId: string;
}

export function WorkflowStrip({ invId, txnId, caseId, scenarioId }: Props) {
  const { t } = useTranslation("workflow");
  const stages = [
    { key: "detect", href: `/investigations/${invId}` },
    { key: "connect", href: `/network/${txnId}` },
    { key: "investigate", href: `/investigations/${invId}` },
    { key: "explain", href: `/investigations/${invId}#ai-h` },
    { key: "simulate", href: `/replay/${scenarioId}` },
    { key: "humanDecision", href: `/cases/${caseId}` },
    { key: "audit", href: `/cases/${caseId}/audit` },
  ];
  return (
    <nav aria-label={t("navLabel")}>
      <ol className="workflow-strip">
        {stages.map((stage) => (
          <li key={stage.key}>
            <Link href={stage.href}>{t(stage.key)}</Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

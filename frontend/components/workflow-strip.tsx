/* Investigation workflow strip: the judge-friendly stage path. Every
 * stage links to the real route that performs it. */

import Link from "next/link";

interface Props {
  invId: string;
  txnId: string;
  caseId: string;
  scenarioId: string;
}

export function WorkflowStrip({ invId, txnId, caseId, scenarioId }: Props) {
  const stages = [
    { label: "Detect", href: `/investigations/${invId}` },
    { label: "Connect", href: `/network/${txnId}` },
    { label: "Investigate", href: `/investigations/${invId}` },
    { label: "Explain", href: `/investigations/${invId}#ai-h` },
    { label: "Simulate", href: `/replay/${scenarioId}` },
    { label: "Human Decision", href: `/cases/${caseId}` },
    { label: "Audit", href: `/cases/${caseId}/audit` },
  ];
  return (
    <nav aria-label="Investigation workflow">
      <ol className="workflow-strip">
        {stages.map((stage) => (
          <li key={stage.label}>
            <Link href={stage.href}>{stage.label}</Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

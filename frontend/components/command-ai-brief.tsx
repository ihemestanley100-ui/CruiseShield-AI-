/* Command Center AI brief. Read-only summary of the latest Muse Spark
 * run from GET case detail: conclusion plus evidence-referenced
 * findings when a run exists, an honest empty state otherwise. Advisory
 * only — never a decision, never a score change. */

import Link from "next/link";
import type { AiAssessment } from "../lib/api";

interface Props {
  assessment: AiAssessment | null;
  invId: string;
}

export function CommandAiBrief({ assessment, invId }: Props) {
  const findings = Array.isArray(assessment?.key_findings)
    ? assessment.key_findings
    : [];
  const missing = Array.isArray(assessment?.missing_information)
    ? assessment.missing_information
    : [];
  return (
    <section className="card command-section" aria-labelledby="ai-brief-h">
      <h2 id="ai-brief-h">Muse Spark brief</h2>
      <p className="muted">
        Advisory only: explains evidence and never constitutes a human
        decision, nor changes risk scores or case status.
      </p>
      {assessment === null ? (
        <>
          <p className="muted" data-testid="ai-brief-empty">
            No Muse Spark analysis is available yet.
          </p>
          <p>
            <Link href={`/investigations/${invId}`}>
              Run analysis from the investigation
            </Link>
          </p>
        </>
      ) : (
        <div data-testid="ai-brief">
          <p>
            <strong>Conclusion: {assessment.conclusion || "—"}</strong>
          </p>
          <ul className="stack">
            {findings.map((finding, index) => (
              <li key={index} className="finding">
                <div>{finding?.finding || "—"}</div>
                <p className="muted">
                  Confidence: {finding?.confidence_label || "—"} ·{" "}
                  {(finding?.evidence_ids ?? []).map((id, i) => (
                    <span key={id}>
                      {i > 0 && ", "}
                      <code>{id}</code>
                    </span>
                  ))}
                </p>
              </li>
            ))}
          </ul>
          {missing.length > 0 && (
            <p className="muted">
              Missing information: {missing.join("; ")}
            </p>
          )}
          <p className="muted">
            {assessment.model_id || "unknown model"} · run{" "}
            <code>{assessment.agent_run_id || "—"}</code> ·{" "}
            {assessment.latency_ms ?? "—"} ms · schema{" "}
            {assessment.schema_validation_status || "—"} · refs{" "}
            {assessment.evidence_reference_validation_status || "—"}
          </p>
        </div>
      )}
    </section>
  );
}

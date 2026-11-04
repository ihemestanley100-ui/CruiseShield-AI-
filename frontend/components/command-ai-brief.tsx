"use client";

/* Command Center AI brief. Read-only summary of the latest Muse Spark
 * run from GET case detail: conclusion plus evidence-referenced
 * findings when a run exists, an honest empty state otherwise. Advisory
 * only — never a decision, never a score change. */

import Link from "next/link";
import type { AiAssessment } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

interface Props {
  assessment: AiAssessment | null;
  invId: string;
}

export function CommandAiBrief({ assessment, invId }: Props) {
  const { t } = useTranslation("command");
  const { t: tCommon } = useTranslation("common");
  const findings = Array.isArray(assessment?.key_findings)
    ? assessment.key_findings
    : [];
  const missing = Array.isArray(assessment?.missing_information)
    ? assessment.missing_information
    : [];
  return (
    <section className="card command-section" aria-labelledby="ai-brief-h">
      <h2 id="ai-brief-h">{t("briefTitle")}</h2>
      <p className="muted">{t("briefAdvisory")}</p>
      {assessment === null ? (
        <>
          <p className="muted" data-testid="ai-brief-empty">
            {t("briefEmpty")}
          </p>
          <p>
            <Link href={`/investigations/${invId}`}>
              {t("runFromInv")}
            </Link>
          </p>
        </>
      ) : (
        <div data-testid="ai-brief">
          <p>
            <strong>
              {t("briefConclusion", { c: assessment.conclusion || "—" })}
            </strong>
          </p>
          <ul className="stack">
            {findings.map((finding, index) => (
              <li key={index} className="finding">
                <div>{finding?.finding || "—"}</div>
                <p className="muted">
                  {t("confPre")}
                  {finding?.confidence_label || "—"} ·{" "}
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
              {t("briefMissing", { list: missing.join("; ") })}
            </p>
          )}
          <p className="muted">
            {t("briefMetaPre", {
              m: assessment.model_id || tCommon("unknownModel"),
            })}
            <code>{assessment.agent_run_id || "—"}</code>{" "}
            {t("briefMetaPost", {
              ms: assessment.latency_ms ?? "—",
              s: assessment.schema_validation_status || "—",
              f: assessment.evidence_reference_validation_status || "—",
            })}
          </p>
        </div>
      )}
    </section>
  );
}

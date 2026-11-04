"use client";

/* Executive KPI row. Every card renders resolved backend values from
 * props; unavailable metrics show "Not available" or "None yet" — never
 * invented counts. Built on the shared Stat primitive. */

import type { AiAssessment } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";
import { Stat } from "./stat";

interface Props {
  invId: string;
  invStatus: string;
  networkBand: string;
  evidenceCount: number;
  latestRun: AiAssessment | null;
  decisionsCount: number;
  caseId: string;
  caseStatus: string;
  txnCount: number | null;
  txnPending: boolean;
}

export function ExecKpis(props: Props) {
  const {
    invId,
    invStatus,
    networkBand,
    evidenceCount,
    latestRun,
    decisionsCount,
    caseId,
    caseStatus,
    txnCount,
    txnPending,
  } = props;
  const { t } = useTranslation("command");
  const { t: tCommon } = useTranslation("common");
  const { t: tNav } = useTranslation("nav");
  const highRisk =
    networkBand === "HIGH" || networkBand === "CRITICAL" ? 1 : 0;
  return (
    <section aria-labelledby="exec-h" className="command-section">
      <h2 id="exec-h">{t("execTitle")}</h2>
      <div className="exec-grid">
        <article className="card kpi-card" aria-label={t("kpiActive")}>
          <Stat
            label={t("kpiActive")}
            value={1}
            caption={t("caseStatusLine", { case: invId, status: invStatus })}
          />
        </article>
        <article className="card kpi-card" aria-label={t("kpiTxn")}>
          <Stat
            label={t("kpiTxn")}
            value={
              txnCount ??
              (txnPending ? tCommon("loading") : tCommon("notAvailable"))
            }
            caption={tNav("synthetic")}
          />
        </article>
        <article className="card kpi-card" aria-label={t("kpiHigh")}>
          <Stat
            label={t("kpiHigh")}
            value={highRisk}
            caption={t("netBandLine", { b: networkBand })}
          />
        </article>
        <article className="card kpi-card" aria-label={t("kpiEvidence")}>
          <Stat
            label={t("kpiEvidence")}
            value={evidenceCount}
            caption={t("linkedTo", { id: invId })}
          />
        </article>
        <article className="card kpi-card" aria-label={t("kpiAi")}>
          <Stat
            label={t("kpiAi")}
            value={latestRun ? latestRun.agent_run_id : tCommon("noneYet")}
            caption={
              latestRun
                ? t("caseStatusLine", {
                    case: latestRun.model_id,
                    status: latestRun.status,
                  })
                : t("noRuns")
            }
          />
        </article>
        <article className="card kpi-card" aria-label={t("kpiDecisions")}>
          <Stat
            label={t("kpiDecisions")}
            value={decisionsCount}
            caption={
              decisionsCount === 0
                ? t("needsAction", { case: caseId, status: caseStatus })
                : t("caseStatusLine", { case: caseId, status: caseStatus })
            }
          />
        </article>
      </div>
    </section>
  );
}

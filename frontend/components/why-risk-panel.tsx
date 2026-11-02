"use client";

import type { RuleResult } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

export function WhyRiskPanel({ rules }: { rules: RuleResult[] }) {
  const { t } = useTranslation("investigation");
  const { t: tCommon } = useTranslation("common");
  return (
    <section className="card" aria-labelledby="why-risk-h">
      <h2 id="why-risk-h">{t("whyRisk")}</h2>
      {rules.length === 0 ? (
        <p className="muted">{t("whyEmpty")}</p>
      ) : (
        <ul className="stack">
          {rules.map((rule) => (
            <li key={rule.rule_result_id} className="rule-row">
              <strong>
                {rule.rule_id} —{" "}
                {rule.triggered ? t("triggered") : t("notTriggered")}
              </strong>
              <p className="muted">{rule.explanation}</p>
              <p className="muted">
                {t("evidenceLabel")}
                <code>{rule.evidence_ids[0] ?? tCommon("none")}</code>
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

"use client";

/* Command Center rule-trigger summary. Compact status chips for every
 * rule result returned by the backend (R-001 through R-008 in the
 * signature scenario); state is always text, never color alone. */

import Link from "next/link";
import type { RuleResult } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

interface Props {
  rules: RuleResult[];
  invId: string;
}

export function CommandRuleSummary({ rules, invId }: Props) {
  const { t } = useTranslation("command");
  const { t: tInv } = useTranslation("investigation");
  const triggered = rules.filter((r) => r.triggered).length;
  return (
    <section className="card command-section" aria-labelledby="rule-sum-h">
      <h2 id="rule-sum-h">{t("rulesTitle")}</h2>
      <p className="muted" data-testid="rule-summary-counts">
        {t("rulesCounts", { a: triggered, b: rules.length })}
      </p>
      {rules.length === 0 ? (
        <p className="muted">{tInv("whyEmpty")}</p>
      ) : (
        <ul className="rule-chips">
          {rules.map((rule) => (
            <li key={rule.rule_result_id} className="rule-chip">
              <span className={`badge ${rule.triggered ? "ok" : ""}`}>
                {rule.rule_id}
              </span>{" "}
              {rule.triggered ? tInv("triggered") : tInv("notTriggered")}
            </li>
          ))}
        </ul>
      )}
      <p>
        <Link href={`/investigations/${invId}`}>
          {t("fullExplanations")}
        </Link>
      </p>
    </section>
  );
}

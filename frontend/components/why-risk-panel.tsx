import type { RuleResult } from "../lib/api";

export function WhyRiskPanel({ rules }: { rules: RuleResult[] }) {
  return (
    <section className="card" aria-labelledby="why-risk-h">
      <h2 id="why-risk-h">Why this risk?</h2>
      {rules.length === 0 ? (
        <p className="muted">No rule results returned for this assessment.</p>
      ) : (
        <ul className="stack">
          {rules.map((rule) => (
            <li key={rule.rule_result_id} className="rule-row">
              <strong>
                {rule.rule_id} —{" "}
                {rule.triggered ? "triggered" : "not triggered"}
              </strong>
              <p className="muted">{rule.explanation}</p>
              <p className="muted">
                Evidence: <code>{rule.evidence_ids[0] ?? "none"}</code>
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

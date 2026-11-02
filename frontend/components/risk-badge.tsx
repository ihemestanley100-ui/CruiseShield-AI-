"use client";

import { useCountUp } from "../lib/use-count-up";
import { useTranslation } from "../lib/i18n/context";

interface RiskBadgeProps {
  score: number;
  band: string;
}

export function RiskBadge({ score, band }: RiskBadgeProps) {
  const { t } = useTranslation("command");
  const display = useCountUp(score);
  return (
    <span
      className={`risk-badge band-${band}`}
      aria-label={t("riskAria", { score, band })}
    >
      <span aria-hidden="true">
        {display}/100 {band}
      </span>
      <span
        className="risk-gauge"
        aria-hidden="true"
        data-testid="risk-gauge"
      >
        <span
          className={`risk-gauge-fill band-fill-${band}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </span>
    </span>
  );
}

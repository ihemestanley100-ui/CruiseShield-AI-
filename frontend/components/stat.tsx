"use client";

/* Shared metric primitive: label + animated value + optional caption.
 * Numbers count up (reduced-motion safe); strings such as
 * "Not available" render as-is. Values always come from props. */

import { useCountUp } from "../lib/use-count-up";

interface Props {
  label: string;
  value: number | string;
  caption?: string;
}

export function Stat({ label, value, caption }: Props) {
  const display = useCountUp(typeof value === "number" ? value : 0);
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      {typeof value === "number" ? (
        <div className="stat-value" aria-label={`${value} ${label}`}>
          <span aria-hidden="true">{display}</span>
        </div>
      ) : (
        <div className="stat-value stat-text">{value}</div>
      )}
      {caption !== undefined && caption !== "" && (
        <div className="stat-caption muted">{caption}</div>
      )}
    </div>
  );
}

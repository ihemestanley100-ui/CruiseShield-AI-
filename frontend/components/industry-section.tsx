"use client";

/* Industry intelligence section. Closed by default; lists the 45
 * canonical industries with registry statuses, then loads honest
 * coverage and evidence readiness per industry on demand. Readiness
 * never promotes a registry status; NOT_READY renders verbatim. */

import type {
  IndustryCoverage,
  IndustryEntry,
  IndustryReadiness,
} from "../lib/api";
import {
  getIndustries,
  getIndustryCoverage,
  getIndustryReadiness,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

type ListState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: IndustryEntry[] }
  | { kind: "error"; message: string };

type DetailState =
  | { kind: "closed" }
  | { kind: "loading"; id: string }
  | { kind: "ready"; coverage: IndustryCoverage; readiness: IndustryReadiness }
  | { kind: "error"; message: string };

export function IndustrySection() {
  const [list, setList] = useState<ListState>({ kind: "closed" });
  const [detail, setDetail] = useState<DetailState>({ kind: "closed" });
  const { t: tCommon } = useTranslation("common");

  function toggleList() {
    if (list.kind !== "closed") {
      setList({ kind: "closed" });
      setDetail({ kind: "closed" });
      return;
    }
    setList({ kind: "loading" });
    getIndustries()
      .then((data) => setList({ kind: "ready", data: data.industries }))
      .catch((err: unknown) =>
        setList({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  function inspect(id: string) {
    setDetail({ kind: "loading", id });
    Promise.all([getIndustryCoverage(id), getIndustryReadiness(id)])
      .then(([coverage, readiness]) =>
        setDetail({ kind: "ready", coverage, readiness })
      )
      .catch((err: unknown) =>
        setDetail({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  return (
    <div>
      <h3>Industry intelligence</h3>
      <button
        type="button"
        aria-expanded={list.kind !== "closed"}
        onClick={toggleList}
      >
        {list.kind === "closed" ? "Show industries" : "Hide industries"}
      </button>
      {list.kind === "loading" && <p role="status">Loading industries…</p>}
      {list.kind === "error" && <p role="alert">{list.message}</p>}
      {list.kind === "ready" && (
        <div>
          <p>{list.data.length} registered industries.</p>
          <ul>
            {list.data.map((entry) => (
              <li key={entry.id}>
                <button type="button" onClick={() => inspect(entry.id)}>
                  {entry.name}
                </button>{" "}
                — {entry.status}
              </li>
            ))}
          </ul>
        </div>
      )}
      {detail.kind === "loading" && (
        <p role="status">Loading {detail.id}…</p>
      )}
      {detail.kind === "error" && <p role="alert">{detail.message}</p>}
      {detail.kind === "ready" && (
        <div>
          <h4>{detail.coverage.name}</h4>
          <p>
            Registry: {detail.coverage.registry_status};{" "}
            {detail.coverage.typologies.length} typologie(s);{" "}
            {detail.coverage.threat_scenarios} threat scenario(s); test:{" "}
            {detail.coverage.test_present
              ? detail.coverage.test_file
              : "missing"}
            .
          </p>
          <p>
            Readiness: <strong>{detail.readiness.overall}</strong> (
            {Object.entries(detail.readiness.checks)
              .map(([check, met]) => `${check}: ${met ? "yes" : "no"}`)
              .join(", ")}
            ).
          </p>
        </div>
      )}
    </div>
  );
}

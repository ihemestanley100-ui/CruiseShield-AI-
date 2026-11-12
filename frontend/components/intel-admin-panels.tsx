"use client";

/* Platform intelligence panels: provider registry, country coverage,
 * live metrics. Lazy closed-by-default; metrics is admin-only
 * server-side and surfaces the denial honestly. */

import {
  getIntelCoverage,
  getIntelMetrics,
  getIntelProviders,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

export function IntelProviderPanel() {
  const { t: tCommon } = useTranslation("common");
  const { t: tEvidence } = useTranslation("evidence");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState("");
  const [error, setError] = useState("");
  const load = () => {
    setOpen(true);
    getIntelProviders().then(
      (body) =>
        setRows(
          body.providers
            .map(
              (p) =>
                `${p.provider_id}: ${p.integration_status}${p.live ? " (LIVE)" : ""}`
            )
            .join(" | ")
        ),
      (err: unknown) => setError(userErrorMessage(err, tCommon))
    );
  };
  return (
    <div>
      <h3>Intelligence providers</h3>
      {!open ? (
        <p>
          <button type="button" onClick={load} aria-expanded={false}>
            {tEvidence("showProv")}
          </button>
        </p>
      ) : error ? (
        <div className="alert error" role="alert">
          {error}
        </div>
      ) : (
        <p className="muted">{rows || tCommon("loading")}</p>
      )}
    </div>
  );
}

export function IntelCoveragePanel() {
  const { t: tCommon } = useTranslation("common");
  const { t: tEvidence } = useTranslation("evidence");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState("");
  const [error, setError] = useState("");
  const load = () => {
    setOpen(true);
    getIntelCoverage().then(
      (body) =>
        setRows(
          body.countries
            .map((c) => `${c.country}: ${c.overall}`)
            .join(" | ") + ` · map: ${body.map_provider}`
        ),
      (err: unknown) => setError(userErrorMessage(err, tCommon))
    );
  };
  return (
    <div>
      <h3>Country coverage</h3>
      {!open ? (
        <p>
          <button type="button" onClick={load} aria-expanded={false}>
            {tEvidence("showProv")}
          </button>
        </p>
      ) : error ? (
        <div className="alert error" role="alert">
          {error}
        </div>
      ) : (
        <p className="muted">{rows || tCommon("loading")}</p>
      )}
    </div>
  );
}

export function IntelMetricsPanel() {
  const { t: tCommon } = useTranslation("common");
  const { t: tEvidence } = useTranslation("evidence");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState("");
  const [error, setError] = useState("");
  const load = () => {
    setOpen(true);
    getIntelMetrics().then(
      (body) =>
        setRows(
          Object.entries(body.counts)
            .map(([k, v]) => `${k}: ${v.total}`)
            .join(" | ")
        ),
      (err: unknown) => setError(userErrorMessage(err, tCommon))
    );
  };
  return (
    <div>
      <h3>Verification activity</h3>
      {!open ? (
        <p>
          <button type="button" onClick={load} aria-expanded={false}>
            {tEvidence("showProv")}
          </button>
        </p>
      ) : error ? (
        <div className="alert error" role="alert">
          {error}
        </div>
      ) : (
        <p className="muted">{rows || tCommon("loading")}</p>
      )}
    </div>
  );
}

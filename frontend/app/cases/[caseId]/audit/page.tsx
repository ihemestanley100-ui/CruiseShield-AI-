"use client";

/* Case audit route. Renders exactly the events returned by
 * GET /api/v1/cases/{id}/audit via the shared AuditList (server order
 * preserved, no invented entries). Same loading/error/not-found states
 * as the parent case route. */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AuditList } from "../../../../components/audit-list";
import { Breadcrumbs } from "../../../../components/breadcrumbs";
import {
  ApiError,
  getCaseAudit,
  type AuditEntry,
} from "../../../../lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; audits: AuditEntry[] }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

export default function CaseAuditPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = params.caseId;
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    getCaseAudit(caseId, controller.signal)
      .then(({ audits }) => setState({ kind: "ready", audits }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === "CASE_NOT_FOUND") {
          setState({ kind: "not-found" });
          return;
        }
        setState({
          kind: "error",
          message:
            err instanceof ApiError
              ? `${err.code}: ${err.message}`
              : err instanceof Error
                ? err.message
                : "request failed",
        });
      });
    return () => controller.abort();
  }, [caseId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: "Command Center", href: "/demo" },
          { label: `Case ${caseId}`, href: `/cases/${caseId}` },
          { label: "Audit trail" },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>Audit trail</h1>
          <p className="muted">Loading audit events…</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>Case not found</h1>
          <p className="muted">
            No case <code>{caseId}</code> exists in the backend.
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>Audit trail</h1>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          </p>
        </section>
      )}
      {state.kind === "ready" && (
        <>
          <div className="page-head">
            <h1>
              Audit trail — Case <code>{caseId}</code>
            </h1>
            <p className="muted">
              Every recorded action on this case, in recorded order.{" "}
              <Link href={`/cases/${caseId}`} className="back-link">
                Back to case
              </Link>
            </p>
          </div>
          <AuditList audits={state.audits} />
        </>
      )}
    </main>
  );
}

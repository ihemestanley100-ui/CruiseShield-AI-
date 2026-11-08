"use client";

/* Case audit route. Renders exactly the events returned by
 * GET /api/v1/cases/{id}/audit via the shared AuditList (server order
 * preserved, no invented entries). Same loading/error/not-found states
 * as the parent case route. */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "../../../../lib/i18n/context";
import { AuditList } from "../../../../components/audit-list";
import { Breadcrumbs } from "../../../../components/breadcrumbs";
import {
  ApiError,
  getCaseAudit,
  userErrorMessage,
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
  const { t } = useTranslation("case");
  const { t: tCommon } = useTranslation("common");
  const { t: tNav } = useTranslation("nav");
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
          message: userErrorMessage(err, tCommon),
        });
      });
    return () => controller.abort();
  }, [caseId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: tNav("commandCenter"), href: "/platform" },
          { label: t("crumb", { id: caseId }), href: `/cases/${caseId}` },
          { label: t("auditCrumb") },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>{t("auditTitle")}</h1>
          <p className="muted">{t("auditLoading")}</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>{t("notFoundTitle")}</h1>
          <p className="muted">
            {t("notFoundPre")}
            <code>{caseId}</code>
            {t("notFoundPost")}
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>{t("auditTitle")}</h1>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              {tCommon("retry")}
            </button>
          </p>
        </section>
      )}
      {state.kind === "ready" && (
        <>
          <div className="page-head">
            <h1>
              {t("auditHeadPre")}
              <code>{caseId}</code>
            </h1>
            <p className="muted">
              {t("auditIntro")}
              <Link href={`/cases/${caseId}`} className="back-link">
                {t("backToCase")}
              </Link>
            </p>
          </div>
          <AuditList audits={state.audits} />
        </>
      )}
    </main>
  );
}

"use client";

/* Batch 4: replay & simulation route. Scenario metadata from
 * GET /api/v1/demo/scenarios, deterministic playback from
 * GET /api/v1/replay, what-if runs from POST /api/v1/simulations.
 * Reset is a deliberate two-step action with stated consequences. */

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Breadcrumbs } from "../../../components/breadcrumbs";
import { ReplayControls } from "../../../components/replay-controls";
import { SimulationPanel } from "../../../components/simulation-panel";
import {
  ApiError,
  getReplay,
  listScenarios,
  resetDemo,
  type DemoResetResult,
} from "../../../lib/api";
import { useTranslation } from "../../../lib/i18n/context";

type State =
  | { kind: "loading" }
  | { kind: "ready"; title: string; defaultTxn: string }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

export default function ReplayPage() {
  const params = useParams<{ scenarioId: string }>();
  const scenarioId = params.scenarioId;
  const { t } = useTranslation("replay");
  const { t: tCommon } = useTranslation("common");
  const { t: tNav } = useTranslation("nav");
  const [state, setState] = useState<State>({ kind: "loading" });
  const [confirming, setConfirming] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetResult, setResetResult] = useState<DemoResetResult | null>(null);
  const [resetError, setResetError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    Promise.all([listScenarios(controller.signal), getReplay(scenarioId, 1, controller.signal)])
      .then(([list, replay]) => {
        const found = list.scenarios.find(
          (s) => s.scenario_id === scenarioId
        );
        if (!found || replay.current_event === null) {
          setState({ kind: "not-found" });
          return;
        }
        setState({
          kind: "ready",
          title: found.title,
          defaultTxn: replay.current_event.transaction.transaction_id,
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === "UNKNOWN_SCENARIO") {
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
                : tCommon("requestFailed"),
        });
      });
    return () => controller.abort();
  }, [scenarioId]);

  async function onReset() {
    setResetting(true);
    setResetError("");
    setResetResult(null);
    try {
      const result = await resetDemo(scenarioId);
      setResetResult(result);
      setConfirming(false);
    } catch (err: unknown) {
      setResetError(
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : err instanceof Error
            ? err.message
            : tCommon("requestFailed")
      );
    } finally {
      setResetting(false);
    }
  }

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: tNav("commandCenter"), href: "/demo" },
          { label: t("crumb", { id: scenarioId }) },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>{t("title", { id: scenarioId })}</h1>
          <p className="muted">{t("loading")}</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>{t("notFoundTitle")}</h1>
          <p className="muted">
            {t("notFoundPre")}
            <code>{scenarioId}</code>
            {t("notFoundPost")}
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>{t("title", { id: scenarioId })}</h1>
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
            <h1>{t("headTitle", { title: state.title })}</h1>
            <p className="muted">
              {t("scenarioPre")}
              <code>{scenarioId}</code>
            </p>
          </div>
          <section className="card" aria-label={t("resetLabel")}>
            <h2>{t("resetTitle")}</h2>
            <p className="muted">{t("resetBlurb")}</p>
            {!confirming && resetResult === null && (
              <button type="button" onClick={() => setConfirming(true)}>
                {t("resetDemo")}
              </button>
            )}
            {confirming && (
              <p>
                <strong>
                  {t("confirmReset", { id: scenarioId })}{" "}
                </strong>
                <button
                  type="button"
                  className="btn-destructive"
                  disabled={resetting}
                  onClick={onReset}
                >
                  {resetting ? t("resetting") : t("confirmResetBtn")}
                </button>{" "}
                <button
                  type="button"
                  className="chip"
                  disabled={resetting}
                  onClick={() => setConfirming(false)}
                >
                  {t("cancel")}
                </button>
              </p>
            )}
            {resetError !== "" && (
              <div className="alert error" role="alert">
                {resetError}
              </div>
            )}
            {resetResult !== null && (
              <div className="alert ok" role="status" data-testid="reset-result">
                {t("resetDonePre")}
                <code>{resetResult.run_id}</code>
                {t("resetDoneMid")}
                <code>{resetResult.seed_hash.slice(0, 12)}…</code>
                {t("resetDonePost")}
              </div>
            )}
          </section>
          <ReplayControls scenarioId={scenarioId} />
          <SimulationPanel defaultTxnId={state.defaultTxn} />
        </>
      )}
    </main>
  );
}

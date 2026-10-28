"""CruiseShield AI hackathon vertical slice: pages + JSON API."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import ai_adapter, cases as cases_mod, evidence as evidence_mod
from app import graph as graph_mod, replay as replay_mod, rules as rules_mod
from app import seed as seed_mod, simulate as simulate_mod
from app.config import META_MODEL_ID, ROOT
from app.models import EvidencePackage, RuleResult
from app.store import Store

APP_VERSION = "1.0.0-p0"

app = FastAPI(title="CruiseShield AI", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
templates.env.globals["naira"] = evidence_mod.kobo_to_naira

store = Store()


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _trace(request: Request) -> str:
    return request.headers.get("x-request-id", uuid.uuid4().hex[:12])


@app.exception_handler(AppError)
async def _app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": str(exc),
                  "trace_id": _trace(request)}})


def _domain_error(exc: ValueError, default_status: int = 400) -> AppError:
    text = str(exc)
    code, _, message = text.partition(":")
    code = code.strip() or "DOMAIN_ERROR"
    status = default_status
    if code in ("CASE_NOT_FOUND", "UNKNOWN_SCENARIO", "UNKNOWN_TRANSACTION",
                "UNKNOWN_EDGE"):
        status = 404
    return AppError(code, message.strip() or text, status)


def _ensure_assessment(txn_id: str) -> tuple[dict, dict, list[dict]]:
    if txn_id in store.state["risk"]:
        risk = store.state["risk"][txn_id]
        return (risk["transaction"], risk["network"],
                store.state["rule_results"][txn_id])
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    trace_id = store.state["trace_id"]
    results = rules_mod.evaluate(txn_id, store.state["transactions"],
                                 store.state["edges"], trace_id)
    as_txn = rules_mod.assess(txn_id, "transaction",
                              store.state["transactions"], store.state["edges"],
                              results, trace_id)
    as_net = rules_mod.assess(txn_id, "network", store.state["transactions"],
                              store.state["edges"], results, trace_id)
    return as_txn, as_net, [r.model_dump() for r in results]


# -- pages ---------------------------------------------------------------
def _page_context(request: Request) -> dict[str, Any]:
    return {"request": request, "app_version": APP_VERSION,
            "scenario_id": store.state["scenario_id"],
            "manifest": store.state["manifest"],
            "model_configured": ai_adapter.configured(),
            "model_id": META_MODEL_ID}


@app.get("/", response_class=HTMLResponse)
def command_center(request: Request):
    primary = store.state["primary_transaction_id"]
    txn = store.get_transaction(primary)
    risk_txn, risk_net, _ = _ensure_assessment(primary)
    ctx = _page_context(request)
    ctx.update({"txn": txn, "risk_txn": risk_txn, "risk_net": risk_net,
                "counts": store.state["manifest"]["expected_graph_counts"],
                "investigations": store.state["investigations"],
                "scenarios": seed_mod.available_scenarios()})
    return templates.TemplateResponse(request, "command.html", ctx)


@app.get("/investigations/{inv_id}", response_class=HTMLResponse)
def investigation_page(request: Request, inv_id: str):
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    txn = store.get_transaction(inv["transaction_id"])
    risk_txn, risk_net, rule_results = _ensure_assessment(inv["transaction_id"])
    case = next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None)
    package = store.state["evidence_packages"][inv_id]
    audits = [a for a in store.state["audits"]
              if a["target_id"] in (inv_id, case["case_id"] if case else "",
                                    inv["alert_id"])][:50]
    ctx = _page_context(request)
    ctx.update({"inv": inv, "txn": txn, "risk_txn": risk_txn,
                "risk_net": risk_net, "rule_results": rule_results,
                "case": case, "package": package,
                "allowed": cases_mod.allowed_transitions(case["status"]) if case else [],
                "decisions": cases_mod.DECISION_LABELS,
                "audits": audits,
                "ai_runs": [r for r in store.state["ai_runs"]
                            if r["evidence_package_id"] == package["package_id"]],
                "simulations": store.state["simulations"],
                "nodes": store.state["nodes"], "edges": store.state["edges"]})
    return templates.TemplateResponse(request, "investigation.html", ctx)


@app.get("/system-health", response_class=HTMLResponse)
def system_health_page(request: Request):
    ctx = _page_context(request)
    ctx.update({"health": health()})
    return templates.TemplateResponse(request, "system_health.html", ctx)


# -- health / demo --------------------------------------------------------
def _counts_now() -> dict[str, int]:
    by_type: dict[str, int] = {}
    for node in store.state["nodes"]:
        by_type[node["node_type"]] = by_type.get(node["node_type"], 0) + 1
    return {"nodes": len(store.state["nodes"]), "edges": len(store.state["edges"]),
            "accounts": by_type.get("account", 0),
            "devices": by_type.get("device", 0),
            "phones": by_type.get("phone", 0),
            "merchants": by_type.get("merchant", 0),
            "beneficiaries": by_type.get("beneficiary", 0),
            "transactions": len(store.state["transactions"]),
            "events": len(store.state["events"])}


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    expected = store.state["manifest"]["expected_graph_counts"]
    actual = _counts_now()
    provenance_bad = graph_mod.validate_provenance(store.state["edges"])
    checks = {
        "store": "PASS" if store.state.get("scenario_id") else "FAIL",
        "seed_integrity": ("PASS" if actual == expected
                           else f"FAIL expected={expected} actual={actual}"),
        "graph_provenance": ("PASS" if not provenance_bad
                             else f"FAIL edges={provenance_bad}"),
        "model_configured": ("PASS" if ai_adapter.configured()
                             else "NOT_CONFIGURED"),
    }
    status = ("healthy" if all(v == "PASS" or k == "model_configured"
                               for k, v in checks.items()) else "degraded")
    return {"status": status, "version": APP_VERSION,
            "scenario_id": store.state["scenario_id"],
            "run_id": store.state["run_id"], "checks": checks}


@app.get("/api/v1/demo/scenarios")
def demo_scenarios() -> dict[str, Any]:
    return {"scenarios": seed_mod.available_scenarios(),
            "active_scenario_id": store.state["scenario_id"]}


@app.post("/api/v1/demo/reset")
def demo_reset(body: dict[str, Any] | None = None) -> dict[str, Any]:
    scenario_id = (body or {}).get("scenario_id", "scn_primary")
    try:
        return store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)


@app.post("/api/v1/demo/scenarios/{scenario_id}/start")
def demo_start(scenario_id: str) -> dict[str, Any]:
    try:
        result = store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


@app.post("/api/v1/demo/judge-start")
def judge_start() -> dict[str, Any]:
    result = store.reset("scn_primary")
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


# -- investigation data ---------------------------------------------------
@app.get("/api/v1/transactions/{txn_id}")
def get_transaction(txn_id: str) -> dict[str, Any]:
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, _ = _ensure_assessment(txn_id)
    return {"transaction": txn, "risk_transaction": risk_txn,
            "risk_network": risk_net}


@app.get("/api/v1/graph/{txn_id}")
def get_graph(txn_id: str) -> dict[str, Any]:
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    # The seeded network is small (22 nodes / 30 edges); Reveal Network
    # returns the full real graph so the demo matches the seed manifest.
    nodes, edges = store.state["nodes"], store.state["edges"]
    return {"transaction_id": txn_id, "nodes": nodes, "edges": edges,
            "provenance_errors": graph_mod.validate_provenance(edges),
            "counts": {"nodes": len(nodes), "edges": len(edges)}}


@app.get("/api/v1/risk/{txn_id}")
def get_risk(txn_id: str, scope: str = "network") -> dict[str, Any]:
    if scope not in ("transaction", "network"):
        raise AppError("UNKNOWN_SCOPE", scope, 400)
    if store.get_transaction(txn_id) is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, rule_results = _ensure_assessment(txn_id)
    return {"assessment": risk_txn if scope == "transaction" else risk_net,
            "rule_results": rule_results}


@app.get("/api/v1/alerts")
def list_alerts() -> dict[str, Any]:
    return {"alerts": store.state["alerts"]}


@app.get("/api/v1/investigations/{inv_id}")
def get_investigation(inv_id: str) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    alert = next(a for a in store.state["alerts"]
                 if a["alert_id"] == inv["alert_id"])
    case = next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None)
    risk_txn, risk_net, rule_results = _ensure_assessment(inv["transaction_id"])
    package = store.state["evidence_packages"][inv_id]
    return {"investigation": inv, "alert": alert,
            "transaction": store.get_transaction(inv["transaction_id"]),
            "risk_transaction": risk_txn, "risk_network": risk_net,
            "rule_results": rule_results, "case": case,
            "evidence_package_id": package["package_id"],
            "evidence_count": len(package["items"])}


@app.post("/api/v1/investigations/{inv_id}/evidence-package")
def build_evidence_package(inv_id: str) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return store.state["evidence_packages"][inv_id]


@app.get("/api/v1/investigations/{inv_id}/evidence-package")
def read_evidence_package(inv_id: str) -> dict[str, Any]:
    return build_evidence_package(inv_id)


@app.post("/api/v1/investigations/{inv_id}/ai-analysis")
async def ai_analysis(inv_id: str, request: Request) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    package = EvidencePackage.model_validate(
        store.state["evidence_packages"][inv_id])
    txn = store.get_transaction(inv["transaction_id"])
    summary = (f"Synthetic investigation {inv_id}: transaction "
               f"{txn['transaction_id']} {txn['sender_account_id']} -> "
               f"{txn['receiver_account_id']} {txn['amount_minor']} kobo.")
    run_id = f"agentrun_{len(store.state['ai_runs']) + 1:04d}"
    trace_id = _trace(request)
    t0 = time.monotonic()
    try:
        run = await ai_adapter.analyze(package, summary,
                                       store.state["trace_id"], run_id)
    except ai_adapter.AIError as exc:
        partial = getattr(exc, "run", None)
        if partial is None:
            partial = {
                "agent_run_id": run_id, "provider": "meta",
                "model_id": META_MODEL_ID,
                "prompt_version": ai_adapter.PROMPT_VERSION,
                "request_id": "", "trace_id": store.state["trace_id"],
                "evidence_package_id": package.package_id,
                "evidence_ids_sent": sorted(i.evidence_id for i in package.items),
                "status": "FAILED", "response_reference": "",
                "schema_validation_status": "NOT_VALIDATED",
                "evidence_reference_validation_status": "NOT_VALIDATED",
                "error_code": exc.code, "synthetic_data_flag": True,
                "latency_ms": 0, "result": {},
            }
        failed = dict(partial)
        if not failed.get("latency_ms"):
            failed["latency_ms"] = int((time.monotonic() - t0) * 1000)
        store.save_ai_run(failed)
        store.append_audit("service", "ai-adapter", "ai.run.failed",
                           "agent_run", run_id, "PENDING", "FAILED",
                           f"{exc.code}: {exc}", store.state["trace_id"], trace_id)
        raise AppError(exc.code, str(exc), 503)
    store.save_ai_run(run)
    store.append_audit("service", "ai-adapter", "ai.run.succeeded",
                       "agent_run", run_id, "PENDING", run["status"],
                       f"Model {run['model_id']} validation "
                       f"{run['schema_validation_status']}/"
                       f"{run['evidence_reference_validation_status']}",
                       store.state["trace_id"], trace_id)
    return run


@app.get("/api/v1/ai-runs/{run_id}")
def get_ai_run(run_id: str) -> dict[str, Any]:
    run = next((r for r in store.state["ai_runs"]
                if r["agent_run_id"] == run_id), None)
    if run is None:
        raise AppError("UNKNOWN_RUN", run_id, 404)
    return run


# -- replay / simulation / cases ------------------------------------------
@app.get("/api/v1/replay/{scenario_id}")
def get_replay(scenario_id: str, cursor: int = 0) -> dict[str, Any]:
    if scenario_id != store.state["scenario_id"]:
        raise AppError("UNKNOWN_SCENARIO", scenario_id, 404)
    return replay_mod.state_at(store.state, cursor)


@app.post("/api/v1/simulations")
def post_simulation(body: dict[str, Any], request: Request) -> dict[str, Any]:
    try:
        sim = simulate_mod.run(
            store.state, body.get("target_transaction_id", ""),
            body.get("ignored_edge_ids", []), body.get("assumption", ""),
            store.state["trace_id"])
    except ValueError as exc:
        raise _domain_error(exc)
    store.save_simulation(sim)
    store.append_audit("human", body.get("actor_id", "investigator"),
                       "simulation.run", "simulation", sim["simulation_id"],
                       f"{sim['baseline_score']}", f"{sim['simulated_score']}",
                       sim["assumption"], store.state["trace_id"],
                       _trace(request))
    return sim


@app.get("/api/v1/cases")
def list_cases() -> dict[str, Any]:
    return {"cases": store.state["cases"]}


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    case = store.get_case(case_id)
    if case is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    decisions = [d for d in store.state["decisions"] if d["case_id"] == case_id]
    return {"case": case, "decisions": decisions,
            "allowed_transitions": cases_mod.allowed_transitions(case["status"])}


@app.post("/api/v1/cases/{case_id}/decisions")
def post_decision(case_id: str, body: dict[str, Any],
                  request: Request) -> dict[str, Any]:
    try:
        record, audit = cases_mod.record_decision(
            store, case_id, body.get("decision", ""),
            body.get("target_status", ""), body.get("reason", ""),
            body.get("actor_id", "investigator"),
            body.get("evidence_viewed", []),
            body.get("recommendation", ""), _trace(request))
    except ValueError as exc:
        raise _domain_error(exc)
    return {"decision": record, "audit": audit,
            "case": store.get_case(case_id)}


@app.get("/api/v1/cases/{case_id}/audit")
def case_audit(case_id: str) -> dict[str, Any]:
    if store.get_case(case_id) is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    return {"audits": [a for a in store.state["audits"]
                       if a["target_id"] == case_id]}


@app.post("/api/v1/events")
def ingest_event(body: dict[str, Any]) -> dict[str, Any]:
    try:
        status, event, warnings = store.ingest_event(body)
    except ValueError as exc:
        raise _domain_error(exc, 422)
    return {"status": status, "event": event, "warnings": warnings}

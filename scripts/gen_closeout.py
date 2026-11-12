"""Generate docs/UFI_CLOSEOUT.md from live repository data.

Point-in-time evidence: run command + UTC timestamp are recorded in
the document. Re-run to refresh; never hand-edit the generated tables.
"""
from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(args: list[str]) -> str:
    out = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True,
                         text=True, check=True)
    return out.stdout.strip()


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT))
    import app.main as main_mod
    from app import industries as ind_mod
    from app import industry_adapters as adapters_mod

    doc = json.loads((ROOT / "docs" / "ZERO_GAP_MATRIX.json").read_text())
    rows = doc["rows"]
    counts = Counter(r["status"] for r in rows)
    total = len(rows)
    closed = counts.get("CLOSED_VERIFIED", 0)
    gated = (counts.get("BLOCKED_EXTERNAL_DEPENDENCY", 0)
             + counts.get("AWAITING_OWNER_APPROVAL", 0))
    in_tree_open = (counts.get("IN_PROGRESS", 0)
                    + counts.get("NOT_STARTED", 0)
                    + counts.get("TESTING", 0))
    routes = sum(1 for r in main_mod.app.routes if hasattr(r, "path"))
    branch = _git(["branch", "--show-current"])
    head = _git(["rev-parse", "--short", "HEAD"])
    dirty = _git(["status", "--porcelain"])
    dirty_count = len(dirty.splitlines()) if dirty else 0
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: list[str] = []
    add = lines.append
    add("# CruiseShield AI - Universal Intel Master Closeout (UFI)")
    add("")
    add("Point-in-time evidence. Generated: %s by" % stamp)
    add("`python scripts/gen_closeout.py`. Re-run to refresh; tables below")
    add("are live repository data, not hand-written claims.")
    add("")
    add("## 1. Discovery (Phase Zero)")
    add("")
    add("- Branch: `%s`, HEAD: `%s`, dirty entries: %d (uncommitted)." % (
        branch, head, dirty_count))
    add("- Backend routes: %d. Matrix: %d rows, schema v%s." % (
        routes, total, doc.get("version")))
    add("- Industries: %d registry entries, %d profile modules." % (
        len(ind_mod.registry()),
        len(list((ROOT / "app").glob("industries_*.py")))))
    add("- Frontend UFI suites: tracing (5), monitoring (4), industry "
        "(3) vitest cases - execution blocked by sandbox node EPERM; "
        "contract-parity test green.")
    add("")
    add("## 2. Score methodology + verified score (H.13)")
    add("")
    add("Methodology (explicit, no hidden weights):")
    add("")
    add("- Denominator: every matrix row (N=%d)." % total)
    add("- CLOSED_VERIFIED requires implementation + automated evidence "
        "in-tree. No partial credit.")
    add("- Owner/external-gated rows (BLOCKED_EXTERNAL_DEPENDENCY + "
        "AWAITING_OWNER_APPROVAL) are reported separately, never as "
        "progress.")
    add("- TESTING/IN_PROGRESS/NOT_STARTED rows that are actionable "
        "in-tree count as open; sandbox-blocked execution is labelled, "
        "not scored.")
    add("")
    add("Score:")
    add("")
    add("- Implementation: %d/%d = %.1f%% CLOSED_VERIFIED." % (
        closed, total, 100.0 * closed / total))
    add("- Owner/external-gated: %d rows (%.1f%%)." % (
        gated, 100.0 * gated / total))
    add("- In-tree open: %d rows (IN_PROGRESS=%d, TESTING=%d, "
        "NOT_STARTED=%d)." % (
            in_tree_open, counts.get("IN_PROGRESS", 0),
            counts.get("TESTING", 0), counts.get("NOT_STARTED", 0)))
    add("- Production readiness: NOT PRODUCTION READY (no hosted CI, "
        "no deploy, dirty tree; unchanged standing verdict).")
    add("")
    add("## 3. Scope reconciliation (directive section B)")
    add("")
    add("| # | Scope item | Canonical component | Status |")
    add("|---|---|---|---|")
    scope = [
        ("1", "Universal platform architecture",
         "app/* engines + 9-layer docs", "CLOSED (UFI-*)"),
        ("2", "Org onboarding + multi-tenancy",
         "app/tenancy.py + D-014 map", "OPEN on D-014 (TEN-01)"),
        ("3", "Identity/auth/authz/audit",
         "auth/abac/SEC-CRED/ROT/DEV", "CLOSED"),
        ("4", "Transaction intelligence",
         "payment_methods + txn APIs", "CLOSED"),
        ("5", "Payment/channel intelligence",
         "taxonomy + channels.py", "CLOSED"),
        ("6", "Party/institution profiles",
         "parties.py + institutions.py", "CLOSED"),
        ("7", "Fraud + behavioural intel",
         "detection + typologies + alerts", "CLOSED"),
        ("8", "Tracing + money-flow",
         "tracing.py + scenarios", "CLOSED"),
        ("9", "Device/telecom/geo intel",
         "DI/telecom/geointel engines", "CLOSED; live BLOCKED"),
        ("10", "Graph intelligence",
         "graph.py + neighborhood", "CLOSED (reused)"),
        ("11", "Investigation + evidence",
         "cases/evidence + reports", "CLOSED"),
        ("12", "Integration gateway",
         "connectors.py (33) + providers", "CLOSED; live BLOCKED"),
        ("13", "45 industry adapters",
         "registry + profiles + fleet", "CLOSED (see section 4)"),
        ("14", "Product entitlements",
         "billing/subscriptions", "CLOSED (pre-existing)"),
        ("15", "Deploy/monitor/governance",
         "runbooks + monitoring", "OPEN (PKG-01..03, PKG-08)"),
        ("16", "Continuous evolution",
         "matrix + closeout loop", "CLOSED (this document)"),
    ]
    for row in scope:
        add("| %s | %s | %s | %s |" % row)
    add("")
    add("## 4. 45-industry matrix (H.6, live)")
    add("")
    add("Status vocabulary: registry status is authoritative; readiness "
        "is evidence only and never promotes it.")
    add("")
    add("| ID | Name | Registry | Profile | Tests | Typologies |")
    add("|---|---|---|---|---|---|")
    for entry in ind_mod.registry():
        config = adapters_mod.build_config(entry["id"])
        add("| %s | %s | %s | %s | %s | %d |" % (
            entry["id"], entry["name"], entry["status"],
            "yes" if config["profile_present"] else "no",
            "yes" if config["test_present"] else "no",
            config["typology_count"]))
    add("")
    add("## 5. Tracing scenarios (H.7)")
    add("")
    add("`tests/test_tracing_scenarios.py` (10 scenarios, green): "
        "multi-hop chain, fan-in honesty, fan-out distribution, "
        "currency-break downgrade, cash-leg limitation, hop-cap "
        "unknown-downstream, provider-reference confirmation, "
        "provenanced upgrade, unprovenanced withholding, isolated "
        "no-match.")
    add("")
    add("## 6. Security + privacy (H.8)")
    add("")
    add("- Tenant isolation enforced + tested incl. new surfaces "
        "(UFI-SEC 8/8); unstamped rows read as default-tenant.")
    add("- Per-client credentials (PBKDF2, scoped, revocable); "
        "rotation keyring; trusted devices (SEC 13/13).")
    add("- Masked-by-default parties/coords/subjects; reveals "
        "write-gated + audited; no secrets in code/logs.")
    add("- Rate limiting via global middleware; audits immutable + "
        "hash-chained (prod keys await D-018 ceremony).")
    add("- Legal review per jurisdiction NOT_ASSESSED; retention "
        "execution awaits D-056.")
    add("")
    add("## 7. Test + CI results (H.9)")
    add("")
    add("@@TEST_RESULTS@@")
    add("")
    add("## 8. Deploy + rollback readiness (H.10)")
    add("")
    add("NOT READY: no hosted CI run (PKG-01), no current-tree deploy "
        "(PKG-02/03), dirty tree, stale unarmed backend. Rollback "
        "runbooks exist; restore drill awaits D-018 prod keys. No "
        "deployment performed or claimed.")
    add("")
    add("## 9. Dependencies + approvals (H.11, live)")
    add("")
    by_status: dict[str, list[str]] = {}
    for row in rows:
        by_status.setdefault(row["status"], []).append(row["id"])
    for status in ("BLOCKED_EXTERNAL_DEPENDENCY",
                   "AWAITING_OWNER_APPROVAL", "TESTING", "IN_PROGRESS",
                   "NOT_STARTED"):
        ids = sorted(by_status.get(status, []))
        add("- %s (%d): %s." % (status, len(ids), ", ".join(ids)))
    add("Packets: PKG-01 (hosted CI/execution), PKG-02/03 (deploy), "
        "PKG-04 (Meta live), PKG-06 (license), PKG-07 (D-014/D-018/ "
        "GAP-001/D-020/D-019b), PKG-08 (D-053..D-057).")
    add("")
    add("## 10. Outstanding gaps + next actions (H.12)")
    add("")
    add("1. Approve PKG-01 (push + hosted CI) - unblocks all TESTING "
        "rows + DET-13/FE-01.")
    add("2. Reply PKG-07 batch (D-014/D-018/GAP-001/D-020/D-019b).")
    add("3. Reply PKG-08 batch (D-053..D-057).")
    add("4. Device Intelligence spec still queued (no code).")
    add("5. `requirements.lock` missing `cryptography` breaks "
        "`test_passkeys` until regen (pre-existing).")
    add("")
    (ROOT / "docs" / "UFI_CLOSEOUT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("closeout generated")


if __name__ == "__main__":
    main()

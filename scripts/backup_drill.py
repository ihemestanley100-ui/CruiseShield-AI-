"""Scratch backup drill: produce -> verify -> restore -> parity.

Test keys are generated fresh every run (never reused, never stored).
The snapshot payload is the canonical deterministic fixture, NOT the
live data/state.json. All artifacts land under --dir (local target).
Prints one JSON evidence object; exits nonzero on any failed gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backups import crypto as crypto_mod
from backups import local_target as local_mod
from backups import produce as produce_mod
from backups import restore as restore_mod
from backups import signing as signing_mod

FIXTURE = (Path(__file__).resolve().parent.parent / "tests" / "fixtures"
           / "canonical-state.json")


def run(drill_dir: Path) -> dict:
    started = time.time()
    dump = FIXTURE.read_bytes()
    doc = json.loads(dump)
    digest = hashlib.sha256(dump).hexdigest()
    audit_log = doc.get("audit_log", [])
    snapshot = produce_mod.Snapshot(
        dump=dump, schema_version="5.1.0",
        table_counts={k: len(v) for k, v in doc.items()
                      if isinstance(v, list)},
        risk={tid: {scope: int(entry["score"]) for scope, entry in
                      scopes.items() if scope in ("transaction", "network")}
              for tid, scopes in doc.get("risk", {}).items()},
        audit={"count": len(audit_log), "head_id": digest[:16]},
        package_hashes={"canonical-state.json": digest})
    recipient_priv, recipient_pub = crypto_mod.generate_keypair()
    seed, verify_key = signing_mod.generate_signing_keypair()
    target = local_mod.LocalDirTarget(drill_dir)
    backup_id, _stamp = produce_mod.new_backup_id()
    report = produce_mod.produce_backup(
        snapshot=snapshot, recipient_pubkeys=[recipient_pub],
        signing_seed=seed, signing_verify_key=verify_key,
        targets={"local": target}, backup_id=backup_id,
        created_at=_stamp, source="scratch")
    verify = restore_mod.verify_backup_set(
        targets={"local": target}, backup_id=backup_id,
        verify_key=verify_key)
    plan = restore_mod.plan_restore(
        target=target, target_name="local", backup_id=backup_id,
        verify_key=verify_key, private_key=recipient_priv)
    parity = hashlib.sha256(plan.plaintext).hexdigest() == hashlib.sha256(
        dump).hexdigest()
    if not parity:
        raise SystemExit("DRILL_PARITY_FAIL")
    return {"drill": "scratch-backup",
            "backup_id": backup_id,
            "bytes": len(dump),
            "sha256": hashlib.sha256(dump).hexdigest(),
            "produce": {"backup_id": report["backup_id"],
                        "promoted": report["promoted"],
                        "checks": report["checks"]},
            "verify": {"targets": verify["targets"],
                       "verified": verify["verified"]},
            "restore_checks": plan.checks,
            "parity": parity,
            "seconds": round(time.time() - started, 2)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run(Path(args.dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

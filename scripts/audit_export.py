"""Audit chain export + verification reports (AUD-01 operator surface).

Keys are operator-supplied and never printed: reports name key ids,
checks, and positions only. Export reads any state file read-only;
verify checks an export file against a keyring file. Prints one JSON
report; exits nonzero when verification fails or inputs are invalid.

No production keys are involved: the D-018 ceremony owns production
signing keys. Tests use ephemeral keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import audit_chain as chain_mod
from migrations.loader import MigrationError, load_audit_keyring


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fail(command: str, code: str, detail: str) -> dict:
    return {"command": command, "ok": False, "error": {
        "code": code, "detail": detail}}


def cmd_export(state_path: str, out_path: str) -> tuple[int, dict]:
    try:
        raw = Path(state_path).read_bytes()
    except OSError:
        return 1, _fail("export", "STATE_NOT_FOUND", state_path)
    try:
        state = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        return 1, _fail("export", "STATE_NOT_JSON", str(exc))
    if not isinstance(state, dict) or "audits" not in state:
        return 1, _fail("export", "STATE_BAD_SHAPE", state_path)
    audits = state["audits"]
    if not isinstance(audits, list):
        return 1, _fail("export", "STATE_BAD_SHAPE", state_path)
    sealed = [a for a in audits if isinstance(a, dict)
              and "audit_digest" in a]
    blob = chain_mod.export_chain(sealed)
    Path(out_path).write_bytes(blob)
    head = sealed[-1].get("audit_digest") if sealed else None
    return 0, {"command": "export", "ok": True, "sealed": len(sealed),
               "legacy_skipped": len(audits) - len(sealed),
               "head_unverified": head,
               "export_sha256": _sha256_bytes(blob), "out": out_path}


def cmd_verify(export_path: str, keyring_path: str) -> tuple[int, dict]:
    try:
        blob = Path(export_path).read_bytes()
    except OSError:
        return 1, _fail("verify", "EXPORT_NOT_FOUND", export_path)
    try:
        doc = json.loads(blob.decode("utf-8"))
    except ValueError as exc:
        return 1, _fail("verify", "EXPORT_NOT_JSON", str(exc))
    records = doc.get("audit_chain") if isinstance(doc, dict) else None
    if not isinstance(records, list) or not all(
            isinstance(r, dict) for r in records):
        return 1, _fail("verify", "EXPORT_BAD_SHAPE", export_path)
    try:
        keyring = load_audit_keyring(keyring_path)
    except MigrationError as exc:
        text = str(exc)
        prefix = exc.code + ": "
        detail = text[len(prefix):] if text.startswith(prefix) else text
        return 1, _fail("verify", exc.code, detail)
    report = chain_mod.verification_report(records, keyring)
    report["command"] = "verify"
    report["export_sha256"] = _sha256_bytes(blob)
    return (0 if report["ok"] else 1), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export and verify tamper-evident audit chains.")
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("export", help="export sealed audits (read-only)")
    ex.add_argument("--state", required=True)
    ex.add_argument("--out", required=True)
    vf = sub.add_parser("verify", help="verify an export vs a keyring")
    vf.add_argument("--export", required=True)
    vf.add_argument("--keyring", required=True)
    args = parser.parse_args(argv)
    if args.command == "export":
        code, report = cmd_export(args.state, args.out)
    else:
        code, report = cmd_verify(args.export, args.keyring)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

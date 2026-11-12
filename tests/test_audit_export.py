"""Audit export + verification reports: operator surface, key-safe.

Socket-free: scratch stores under tmp_path, ephemeral keys, CLI
driven via main(argv) with capsys. No production keys involved
(D-018 owns the ceremony); every failure test also asserts key
material never reaches the printed report.
"""
import hashlib
import json
import sys

sys.path.insert(0, "scripts")
import audit_export as exporter

from app import audit_chain as chain_mod
from app.store import Store

KEY = b"e" * 32


def _audit(store, action="case.decision"):
    return store.append_audit("human", "u1", action, "case", "c1",
                              "NEW", "TRIAGED", "reason", "t", "t")


def _sealed_state(tmp_path, legacy=1, sealed=3):
    store = Store(tmp_path / "s.json")
    for _ in range(legacy):
        _audit(store)
    store.audit_chain_key = KEY
    for _ in range(sealed):
        _audit(store)
    return tmp_path / "s.json"


def _keyring_file(tmp_path, keys):
    path = tmp_path / "keyring.json"
    path.write_text(json.dumps({k: v.hex() for k, v in keys.items()}),
                    encoding="utf-8")
    return path


def _run(argv, capsys):
    code = exporter.main(argv)
    return code, json.loads(capsys.readouterr().out)


def test_export_writes_canonical_bytes_and_report(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    code, report = _run(["export", "--state", str(state),
                         "--out", str(out)], capsys)
    audits = json.loads(state.read_bytes())["audits"]
    assert code == 0
    assert report["ok"] is True
    assert report["sealed"] == 3
    assert report["legacy_skipped"] == len(audits) - 3
    blob = out.read_bytes()
    assert blob == chain_mod.export_chain(
        [a for a in json.loads(state.read_bytes())["audits"]
         if "audit_digest" in a])
    assert report["export_sha256"] == hashlib.sha256(blob).hexdigest()
    assert report["head_unverified"] == json.loads(
        blob)["audit_chain"][-1]["audit_digest"]


def test_export_legacy_only_reports_zero_sealed(tmp_path, capsys):
    store = Store(tmp_path / "s.json")
    _audit(store)
    out = tmp_path / "chain.export.json"
    code, report = _run(["export", "--state", str(tmp_path / "s.json"),
                         "--out", str(out)], capsys)
    audits = json.loads((tmp_path / "s.json").read_bytes())["audits"]
    assert code == 0
    assert report["sealed"] == 0
    assert report["legacy_skipped"] == len(audits)
    assert report["head_unverified"] is None


def test_verify_round_trip_passes(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    assert _run(["export", "--state", str(state),
                 "--out", str(out)], capsys)[0] == 0
    keyring = _keyring_file(tmp_path, {"k1": KEY})
    code, report = _run(["verify", "--export", str(out),
                         "--keyring", str(keyring)], capsys)
    assert code == 0
    assert report["ok"] is True
    assert report["sealed"] == 3
    assert report["key_ids"] == ["k1"]
    assert report["error"] is None
    assert report["export_sha256"] == hashlib.sha256(
        out.read_bytes()).hexdigest()


def test_verify_detects_tamper_without_leaking_key(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    assert _run(["export", "--state", str(state),
                 "--out", str(out)], capsys)[0] == 0
    doc = json.loads(out.read_bytes())
    doc["audit_chain"][1]["reason"] = "forged!"
    out.write_bytes(json.dumps(doc).encode("utf-8"))
    keyring = _keyring_file(tmp_path, {"k1": KEY})
    code, report = _run(["verify", "--export", str(out),
                         "--keyring", str(keyring)], capsys)
    assert code == 1
    assert report["ok"] is False
    assert report["error"]["code"] == "AUDIT_CHAIN_INVALID"
    assert "AUDIT_TAMPER" in report["error"]["detail"]
    assert KEY.hex() not in json.dumps(report)


def test_verify_unknown_key_id_names_id_not_key(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    assert _run(["export", "--state", str(state),
                 "--out", str(out)], capsys)[0] == 0
    keyring = _keyring_file(tmp_path, {"other": KEY})
    code, report = _run(["verify", "--export", str(out),
                         "--keyring", str(keyring)], capsys)
    assert code == 1
    assert "AUDIT_KEY_UNKNOWN" in report["error"]["detail"]
    assert KEY.hex() not in json.dumps(report)


def test_verify_rejects_bad_export_shape(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{"nope": []}', encoding="utf-8")
    keyring = _keyring_file(tmp_path, {"k1": KEY})
    code, report = _run(["verify", "--export", str(bad),
                         "--keyring", str(keyring)], capsys)
    assert code == 1
    assert report["error"]["code"] == "EXPORT_BAD_SHAPE"


def test_verify_missing_keyring(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    assert _run(["export", "--state", str(state),
                 "--out", str(out)], capsys)[0] == 0
    code, report = _run(["verify", "--export", str(out), "--keyring",
                         str(tmp_path / "nope.json")], capsys)
    assert code == 1
    assert report["error"]["code"] == "KEYRING_NOT_FOUND"


def test_verify_short_key_rejected(tmp_path, capsys):
    state = _sealed_state(tmp_path)
    out = tmp_path / "chain.export.json"
    assert _run(["export", "--state", str(state),
                 "--out", str(out)], capsys)[0] == 0
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"k1": "abcd"}), encoding="utf-8")
    code, report = _run(["verify", "--export", str(out),
                         "--keyring", str(short)], capsys)
    assert code == 1
    assert report["error"]["code"] == "KEYRING_KEY_TOO_SHORT"


def test_export_missing_state(tmp_path, capsys):
    code, report = _run(["export", "--state",
                         str(tmp_path / "nope.json"), "--out",
                         str(tmp_path / "o.json")], capsys)
    assert code == 1
    assert report["error"]["code"] == "STATE_NOT_FOUND"


def test_verification_report_unit_shape(tmp_path):
    store = Store(tmp_path / "s.json")
    store.audit_chain_key = KEY
    _audit(store)
    _audit(store)
    sealed = [a for a in store.state["audits"] if "audit_digest" in a]
    good = chain_mod.verification_report(sealed, {"k1": KEY},
                                         legacy_skipped=2)
    assert good == {"ok": True, "sealed": 2, "legacy_skipped": 2,
                    "head": sealed[-1]["audit_digest"], "key_ids": ["k1"],
                    "error": None}
    sealed[0]["reason"] = "forged!"
    bad = chain_mod.verification_report(sealed, {"k1": KEY})
    assert bad["ok"] is False
    assert bad["head"] is None
    assert bad["error"]["code"] == "AUDIT_CHAIN_INVALID"
    assert "AUDIT_TAMPER" in bad["error"]["detail"]

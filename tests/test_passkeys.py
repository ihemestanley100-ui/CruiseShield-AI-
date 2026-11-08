"""D-045 passkeys: ceremonies with real ECDSA/EdDSA vectors. Socket-free."""
import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, utils
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import passkeys as pk_mod
from app import ratelimit as rl
from app.auth import b64d, b64e

SECRET = "test-secret-passkey-032-chars!!!"
RECORD = auth_mod.hash_password("demo-pass-1")
RP_ID = "shield.example"
RP_ORIGIN = "https://shield.example"


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", "")
    monkeypatch.setattr(config_mod, "PASSKEYS_ENABLED", "1")
    monkeypatch.setattr(config_mod, "RP_ID", RP_ID)
    monkeypatch.setattr(config_mod, "RP_ORIGIN", RP_ORIGIN)
    return monkeypatch


def _req(cookie=None):
    hdrs = [(b"host", b"t")]
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _cookie(resp):
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _login(user, password="demo-pass-1"):
    return _cookie(main.auth_login({"username": user,
                                    "password": password}, _req()))


# --- minimal deterministic CBOR encoder (test vectors only) -------------


def _head(major, n):
    if n < 24:
        return bytes([(major << 5) | n])
    for width, code in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if n < 256 ** width:
            return bytes([(major << 5) | code]) + n.to_bytes(width,
                                                             "big")
    raise AssertionError("too big")


def cbor(value):
    if value is True:
        return b"\xf5"
    if value is False:
        return b"\xf4"
    if value is None:
        return b"\xf6"
    if isinstance(value, int):
        if value >= 0:
            return _head(0, value)
        return _head(1, -1 - value)
    if isinstance(value, bytes):
        return _head(2, len(value)) + value
    if isinstance(value, str):
        raw = value.encode()
        return _head(3, len(raw)) + raw
    if isinstance(value, (list, tuple)):
        return _head(4, len(value)) + b"".join(cbor(v) for v in value)
    if isinstance(value, dict):
        out = _head(5, len(value))
        for key, val in value.items():
            out += cbor(key) + cbor(val)
        return out
    raise AssertionError(type(value))


def _ec_key():
    priv = ec.generate_private_key(ec.SECP256R1())
    nums = priv.public_key().public_numbers()
    return priv, {"alg": -7, "x": nums.x.to_bytes(32, "big"),
                  "y": nums.y.to_bytes(32, "big")}


def _ed_key():
    priv = ed25519.Ed25519PrivateKey.generate()
    return priv, {"alg": -8,
                  "x": priv.public_key().public_bytes_raw()}


def _cose(key):
    if key["alg"] == -7:
        return {1: 2, 3: -7, -1: 1, -2: key["x"], -3: key["y"]}
    return {1: 1, 3: -8, -1: 6, -2: key["x"]}


def _auth_data(cred_id=None, cose=None, count=0, flags=0x41,
               rp_id=RP_ID):
    out = hashlib.sha256(rp_id.encode()).digest() + bytes([flags]) \
        + count.to_bytes(4, "big")
    if cred_id is not None:
        out += b"\x00" * 16 + len(cred_id).to_bytes(2, "big") \
            + cred_id + cbor(cose)
    return out


def _client_data(typ, challenge_b64, origin=RP_ORIGIN):
    return json.dumps({"type": typ, "challenge": challenge_b64,
                       "origin": origin},
                      separators=(",", ":")).encode()


def _raw_es256(priv, data):
    der = priv.sign(data, ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def _register(cookie, key=None, priv=None, cred_id=None, rp_id=RP_ID,
              origin=RP_ORIGIN, flags=0x41, fmt="none", att_extra=None):
    if key is None:
        priv, key = _ec_key()
    cid = cred_id if cred_id is not None else b"cred-id-01234567"
    opts = main.passkey_register_options({}, _req(cookie))
    auth_data = _auth_data(cid, _cose(key), flags=flags, rp_id=rp_id)
    client_raw = _client_data("webauthn.create", opts["challenge"],
                              origin)
    statement = dict(att_extra or {})
    if fmt == "packed":
        statement.setdefault("alg", -7)
        statement.setdefault("sig", _raw_es256(
            priv, auth_data + hashlib.sha256(client_raw).digest()))
    attestation = cbor({"fmt": fmt, "authData": auth_data,
                        "attStmt": statement})
    return main.passkey_register_verify(
        {"response": {"type": "public-key", "id": b64e(cid),
                      "response": {
                          "clientDataJSON": b64e(client_raw),
                          "attestationObject": b64e(attestation)}},
         "challenge_id": opts["challenge_id"]}, _req(cookie))


def _assert(cookie_user, priv, cred_id_b64, count, origin=RP_ORIGIN,
            flags=0x01):
    opts = main.passkey_auth_options({"username": cookie_user}, _req())
    auth_data = _auth_data(count=count, flags=flags)
    client_raw = _client_data("webauthn.get", opts["challenge"], origin)
    signed = auth_data + hashlib.sha256(client_raw).digest()
    if isinstance(priv, ed25519.Ed25519PrivateKey):
        sig = priv.sign(signed)
    else:
        sig = _raw_es256(priv, signed)
    return main.passkey_auth_verify(
        {"username": cookie_user,
         "response": {"type": "public-key", "id": cred_id_b64,
                      "response": {
                          "clientDataJSON": b64e(client_raw),
                          "authenticatorData": b64e(auth_data),
                          "signature": b64e(sig)}},
         "challenge_id": opts["challenge_id"]}, _req())


def test_register_options_shape(tmp_store, armed):
    cookie = _login("judge")
    opts = main.passkey_register_options({}, _req(cookie))
    assert opts["rp"] == {"id": RP_ID, "name": "CruiseShield AI"}
    assert opts["attestation"] == "none"
    assert [p["alg"] for p in opts["pubKeyCredParams"]] == [-7, -8]
    assert opts["excludeCredentials"] == []
    assert opts["user"]["name"] == "judge"


def test_register_none_success(tmp_store, armed):
    cookie = _login("judge")
    body = _register(cookie)
    assert tmp_store.passkey_credential(
        body["credential_id"])["user"] == "judge"
    listed = main.list_passkeys(_req(cookie))["credentials"]
    assert len(listed) == 1 and "cose" not in listed[0]
    assert any(a["action"] == "passkey.register"
               for a in tmp_store.state["audits"])
    opts = main.passkey_register_options({}, _req(cookie))
    assert len(opts["excludeCredentials"]) == 1


def test_register_ed25519_and_packed(tmp_store, armed):
    cookie = _login("judge")
    priv, key = _ed_key()
    out = _register(cookie, key=key, cred_id=b"ed-credential-01")
    assert tmp_store.passkey_credential(
        out["credential_id"])["cose"]["alg"] == -8
    priv2, key2 = _ec_key()
    out2 = _register(cookie, key=key2, priv=priv2,
                     cred_id=b"packed-cred-0001", fmt="packed")
    assert tmp_store.passkey_credential(
        out2["credential_id"]) is not None


def test_register_rejects(tmp_store, armed):
    cookie = _login("judge")
    with pytest.raises(main.AppError) as exc:
        _register(cookie, origin="https://evil.example")
    assert exc.value.code == "ORIGIN_MISMATCH"
    with pytest.raises(main.AppError) as exc:
        _register(cookie, rp_id="other.example",
                  cred_id=b"rp-mismatch-0001")
    assert exc.value.code == "RP_MISMATCH"
    with pytest.raises(main.AppError) as exc:
        _register(cookie, flags=0x40, cred_id=b"no-up-flag-00001")
    assert exc.value.code == "USER_NOT_PRESENT"
    with pytest.raises(main.AppError) as exc:
        _register(cookie, fmt="tpm", cred_id=b"tpm-fmt-00000001")
    assert exc.value.code == "ATTESTATION_UNSUPPORTED"
    with pytest.raises(main.AppError) as exc:
        _register(cookie, fmt="packed",
                  att_extra={"x5c": [b"cert"], "sig": b"s" * 64},
                  cred_id=b"x5c-present-00001")
    assert exc.value.code == "ATTESTATION_CA_UNSUPPORTED"


def test_register_duplicate_and_bad_key(tmp_store, armed):
    cookie = _login("judge")
    first = _register(cookie, cred_id=b"dupe-credential-1")
    with pytest.raises(main.AppError) as exc:
        _register(cookie, cred_id=b"dupe-credential-1")
    assert exc.value.code == "CREDENTIAL_DUPLICATE"
    assert first["credential_id"]
    opts = main.passkey_register_options({}, _req(cookie))
    bad_cose = {1: 2, 3: -257, -1: 1, -2: b"x" * 32, -3: b"y" * 32}
    auth_data = _auth_data(b"rs256-credential", bad_cose)
    client_raw = _client_data("webauthn.create", opts["challenge"])
    attestation = cbor({"fmt": "none", "authData": auth_data,
                        "attStmt": {}})
    with pytest.raises(main.AppError) as exc:
        main.passkey_register_verify(
            {"response": {"type": "public-key", "id": "x",
                          "response": {
                              "clientDataJSON": b64e(client_raw),
                              "attestationObject": b64e(attestation)}},
             "challenge_id": opts["challenge_id"]}, _req(cookie))
    assert exc.value.code == "KEY_UNSUPPORTED"


def test_authenticate_success(tmp_store, armed):
    cookie = _login("judge")
    priv, key = _ec_key()
    out = _register(cookie, key=key, priv=priv,
                    cred_id=b"authn-credential")
    resp = _assert("judge", priv, out["credential_id"], 1)
    assert resp.status_code == 200
    assert main.auth_me(_req(_cookie(resp)))["user"] == "judge"
    assert tmp_store.passkey_credential(
        out["credential_id"])["sign_count"] == 1
    assert any(a["action"] == "auth.login.passkey"
               for a in tmp_store.state["audits"])


def test_authenticate_ed25519(tmp_store, armed):
    cookie = _login("judge")
    priv, key = _ed_key()
    out = _register(cookie, key=key, cred_id=b"ed-authn-cred-001")
    resp = _assert("judge", priv, out["credential_id"], 1)
    assert resp.status_code == 200


def test_assertion_clone_and_tamper(tmp_store, armed):
    cookie = _login("judge")
    priv, key = _ec_key()
    out = _register(cookie, key=key, priv=priv,
                    cred_id=b"clone-credential")
    cid = out["credential_id"]
    _assert("judge", priv, cid, 1)
    with pytest.raises(main.AppError) as exc:
        _assert("judge", priv, cid, 1)
    assert exc.value.code == "CLONE_SUSPECTED"
    opts = main.passkey_auth_options({"username": "judge"}, _req())
    auth_data = _auth_data(count=2, flags=0x01)
    client_raw = _client_data("webauthn.get", opts["challenge"])
    with pytest.raises(main.AppError) as exc:
        main.passkey_auth_verify(
            {"username": "judge",
             "response": {"type": "public-key", "id": cid,
                          "response": {
                              "clientDataJSON": b64e(client_raw),
                              "authenticatorData": b64e(auth_data),
                              "signature": b64e(b"\x00" * 64)}},
             "challenge_id": opts["challenge_id"]}, _req())
    assert exc.value.code == "SIGNATURE_INVALID"


def test_assertion_rejects(tmp_store, armed):
    cookie = _login("judge")
    priv, key = _ec_key()
    out = _register(cookie, key=key, priv=priv,
                    cred_id=b"reject-credential")
    with pytest.raises(main.AppError) as exc:
        _assert("judge", priv, "no-such-id", 1)
    assert exc.value.code == "CREDENTIAL_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        _assert("judge", priv, out["credential_id"], 1,
                origin="https://evil.example")
    assert exc.value.code == "ORIGIN_MISMATCH"
    with pytest.raises(main.AppError) as exc:
        _assert("judge", priv, out["credential_id"], 1, flags=0x00)
    assert exc.value.code == "USER_NOT_PRESENT"
    opts = main.passkey_auth_options({"username": "judge"}, _req())
    client_raw = _client_data("webauthn.get", opts["challenge"])
    with pytest.raises(main.AppError) as exc:
        main.passkey_auth_verify(
            {"username": "judge",
             "response": {"type": "public-key",
                          "id": out["credential_id"],
                          "response": {
                              "clientDataJSON": b64e(client_raw),
                              "authenticatorData": b64e(b"\x00" * 10),
                              "signature": b64e(b"\x00" * 64)}},
             "challenge_id": opts["challenge_id"]}, _req())
    assert exc.value.code == "AUTH_DATA_SHORT"


def test_challenge_single_use_expiry_foreign(tmp_store, armed):
    cookie = _login("judge")
    opts = main.passkey_register_options({}, _req(cookie))
    tmp_store.take_passkey_challenge(opts["challenge_id"])
    with pytest.raises(main.AppError) as exc:
        main.passkey_register_verify(
            {"response": {"type": "public-key"}, "challenge_id": "dead"},
            _req(cookie))
    assert exc.value.code == "CHALLENGE_UNKNOWN"
    tmp_store.save_passkey_challenge(
        "cid-old", {"user": "judge", "purpose": "register",
                    "challenge": "x", "exp": 1000.0})
    with pytest.raises(main.AppError) as exc:
        main.passkey_register_verify(
            {"response": {"type": "public-key", "id": "x",
                          "response": {"clientDataJSON": "e30",
                                       "attestationObject": "e30"}},
             "challenge_id": "cid-old"}, _req(cookie))
    assert exc.value.code == "CHALLENGE_EXPIRED"


def test_flag_off_and_misconfig(tmp_store, armed):
    cookie = _login("judge")
    armed.setattr(config_mod, "PASSKEYS_ENABLED", "0")
    with pytest.raises(main.AppError) as exc:
        main.passkey_register_options({}, _req(cookie))
    assert exc.value.code == "PASSKEYS_DISABLED"
    armed.setattr(config_mod, "PASSKEYS_ENABLED", "1")
    armed.setattr(config_mod, "RP_ID", "")
    with pytest.raises(main.AppError) as exc:
        main.passkey_auth_options({"username": "judge"}, _req())
    assert exc.value.code == "PASSKEYS_MISCONFIGURED"


def test_options_throttled_and_no_credentials(tmp_store, armed):
    for _ in range(10):
        with pytest.raises(main.AppError):
            main.passkey_auth_options({"username": "ghost"}, _req())
    resp = main.passkey_auth_options({"username": "ghost"}, _req())
    assert resp.status_code == 429


def test_remove_credential(tmp_store, armed):
    cookie = _login("judge")
    out = _register(cookie, cred_id=b"remove-credential")
    boss = _login("boss")
    with pytest.raises(main.AppError) as exc:
        main.remove_passkey({"credential_id": out["credential_id"]},
                            _req(boss))
    assert exc.value.code == "CREDENTIAL_UNKNOWN"
    body = main.remove_passkey({"credential_id": out["credential_id"]},
                               _req(cookie))
    assert body == {"ok": True, "removed": True}
    with pytest.raises(main.AppError) as exc:
        main.remove_passkey({"credential_id": out["credential_id"]},
                            _req(cookie))
    assert exc.value.code == "CREDENTIAL_UNKNOWN"


def test_fail_closed_without_crypto(tmp_store, armed, monkeypatch):
    cookie = _login("judge")
    priv, key = _ec_key()
    out = _register(cookie, key=key, priv=priv,
                    cred_id=b"nocrypto-cred-001")
    monkeypatch.setattr(pk_mod, "_CRYPTO", False)
    with pytest.raises(main.AppError) as exc:
        _assert("judge", priv, out["credential_id"], 1)
    assert exc.value.code == "SIGNATURE_INVALID"


def test_passkey_login_pending_when_totp_required(tmp_store, armed):
    armed.setattr(config_mod, "MFA_REQUIRED_ROLES", "investigator")
    cookie = _login("judge")
    body = json.loads(main.auth_login(
        {"username": "judge", "password": "demo-pass-1"},
        _req()).body.decode())
    assert body["mfa_pending"] is True
    priv, key = _ec_key()
    out = _register(cookie, key=key, priv=priv,
                    cred_id=b"pending-cred-0001")
    resp = _assert("judge", priv, out["credential_id"], 1)
    assert json.loads(resp.body.decode())["mfa_pending"] is True

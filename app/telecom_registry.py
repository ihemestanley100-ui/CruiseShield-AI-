"""Global operator registry (Telecom Identity, versioned + provenance-labeled).

Normalized registry across NG/KE/ZW/ZA/US/UK/FR. Every record carries
provenance and confidence; network codes come from public ITU/national
allocations and are NOT live-verified. Number ranges are ALLOCATION
ranges only — in portable markets they never prove the current
operator. Per-operator API availability is explicit; nothing is
assumed CONNECTED (see app/telecom_providers.py for live status).
"""
from __future__ import annotations

import re
from typing import Any

REGISTRY_VERSION = "1.0"
REGISTRY_UPDATED = "2026-11-07"
REGISTRY_PROVENANCE = "public-itu-ncc-allocations-unverified"

# CAMARA / operator APIs tracked per operator. Status vocabulary:
# NOT_CONNECTED (default), CONNECTED (only with creds+handshake+evidence),
# NOT_APPLICABLE (e.g. MTN-only API on a non-MTN operator).
TRACKED_APIS = (
    "camara_number_verification",
    "camara_sim_swap",
    "camara_device_swap",
    "camara_kyc_match",
    "camara_number_recycling",
    "camara_device_identifier",
    "mtn_sim_verification",
    "hlr_lookup",
)

E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
NG_LOCAL_RE = re.compile(r"^0([789]\d)(\d{8})$")

CALLING_CODES = {
    "234": "NG", "1": "US", "44": "UK", "33": "FR",
    "254": "KE", "263": "ZW", "27": "ZA",
}

COUNTRY_NAMES = {
    "NG": "Nigeria", "KE": "Kenya", "ZW": "Zimbabwe",
    "ZA": "South Africa", "US": "United States",
    "UK": "United Kingdom", "FR": "France",
}


def _apis(except_connected: None = None,
          not_applicable: tuple[str, ...] = ()) -> dict[str, dict]:
    _ = except_connected
    out = {}
    for name in TRACKED_APIS:
        if name in not_applicable:
            out[name] = {"status": "NOT_APPLICABLE",
                         "note": "operator out of API scope"}
        else:
            out[name] = {"status": "NOT_CONNECTED",
                         "note": "no credentials, handshake, or evidence"}
    return out


def _op(operator_id: str, country: str, name: str,
        aliases: tuple[str, ...], mcc_mnc: tuple[str, ...],
        ranges: tuple[str, ...], portability: bool | str,
        range_note: str,
        not_applicable: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "operator_id": operator_id, "country": country,
        "country_name": COUNTRY_NAMES[country], "name": name,
        "aliases": list(aliases), "mcc_mnc": list(mcc_mnc),
        "number_ranges": list(ranges), "range_note": range_note,
        "portability_support": portability, "apis": _apis(
            not_applicable=not_applicable),
        "coverage_status": "registry-only",
        "provenance": {"source": REGISTRY_PROVENANCE,
                       "confidence": "MEDIUM",
                       "registry_version": REGISTRY_VERSION,
                       "updated": REGISTRY_UPDATED},
    }


_MTN_ONLY = ("mtn_sim_verification",)

OPERATORS: tuple[dict[str, Any], ...] = (
    _op("mtn-ng", "NG", "MTN Nigeria", ("MTN", "MTN NG"), ("621-30",),
        ("0803", "0806", "0703", "0706", "0813", "0816", "0810",
         "0814", "0903", "0906", "0913", "0916"), True,
        "NCC allocation prefixes; MNP portability applies — allocation "
        "never proves the current operator."),
    _op("glo-ng", "NG", "Globacom", ("Glo", "GLOBACOM"), ("621-50",),
        ("0805", "0807", "0705", "0815", "0811", "0905"), True,
        "NCC allocation prefixes; MNP portability applies — allocation "
        "never proves the current operator."),
    _op("airtel-ng", "NG", "Airtel Nigeria", ("Airtel",), ("621-20",),
        ("0802", "0808", "0708", "0812", "0701", "0902", "0901",
         "0904", "0912"), True,
        "NCC allocation prefixes; MNP portability applies — allocation "
        "never proves the current operator."),
    _op("t2-ng", "NG", "T2 (9mobile)", ("9mobile", "9MOBILE", "T2"),
        ("621-60",), ("0809", "0817", "0818", "0909", "0908"), True,
        "NCC allocation prefixes; MNP portability applies — allocation "
        "never proves the current operator."),
    _op("safaricom-ke", "KE", "Safaricom", (), ("639-02",), (), True,
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for KE."),
    _op("econet-zw", "ZW", "Econet Zimbabwe", ("Econet",), ("648-01",),
        (), "unknown",
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for ZW."),
    _op("mtn-za", "ZA", "MTN South Africa", ("MTN",), ("655-10",), (),
        True,
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for ZA."),
    _op("vodacom-za", "ZA", "Vodacom South Africa", ("Vodacom",),
        ("655-01",), (), True,
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for ZA."),
    _op("tmobile-us", "US", "T-Mobile US", ("T-Mobile", "TMOBILE"),
        ("310-260",), (), True,
        "NANP numbers are pooled and portable; no operator ranges exist.",
        not_applicable=_MTN_ONLY),
    _op("verizon-us", "US", "Verizon", (), ("311-480",), (), True,
        "NANP numbers are pooled and portable; no operator ranges exist.",
        not_applicable=_MTN_ONLY),
    _op("att-us", "US", "AT&T", ("ATT",), ("310-410",), (), True,
        "NANP numbers are pooled and portable; no operator ranges exist.",
        not_applicable=_MTN_ONLY),
    _op("vodafone-uk", "UK", "Vodafone UK", ("Vodafone",), ("234-15",),
        (), True,
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for UK.",
        not_applicable=_MTN_ONLY),
    _op("orange-fr", "FR", "Orange France", ("Orange",), ("208-01",),
        (), True,
        "Per-operator ranges unavailable in this registry version; "
        "allocation lookup returns UNKNOWN for FR.",
        not_applicable=_MTN_ONLY),
)

_BY_ID = {op["operator_id"]: op for op in OPERATORS}


def registry_version() -> dict[str, str]:
    return {"version": REGISTRY_VERSION, "updated": REGISTRY_UPDATED,
            "operators": str(len(OPERATORS))}


def list_operators(country: str | None = None) -> list[dict[str, Any]]:
    import copy

    ops = list(OPERATORS)
    if country:
        code = (country or "").strip().upper()
        ops = [op for op in ops if op["country"] == code]
    return copy.deepcopy(ops)


def get_operator(operator_id: str) -> dict[str, Any] | None:
    import copy

    op = _BY_ID.get((operator_id or "").strip().lower())
    return copy.deepcopy(op) if op else None


def normalize_e164(raw: str) -> str:
    """Normalize to E.164; raise ValueError when unparseable.

    Accepts E.164 (+<cc><number>, max 15 digits) and Nigerian local
    11-digit mobile form (0[789]0xxxxxxx -> +234...). Nothing else is
    guessed: unknown shapes are rejected, never coerced.
    """
    if not isinstance(raw, str):
        raise ValueError("INVALID_E164: %r" % (raw,))
    text = raw.strip().replace(" ", "").replace("-", "")
    if E164_RE.match(text):
        return text
    local = NG_LOCAL_RE.match(text)
    if local:
        return "+234" + local.group(1) + local.group(2)
    raise ValueError("INVALID_E164: %r" % (raw,))


def country_for_e164(e164: str) -> str | None:
    """Calling-code -> ISO country, longest-prefix match first."""
    digits = e164.lstrip("+")
    for code in sorted(CALLING_CODES, key=len, reverse=True):
        if digits.startswith(code):
            return CALLING_CODES[code]
    return None


def allocation_lookup(e164: str) -> dict[str, Any]:
    """Allocation-range operator match (NOT current-operator proof).

    Returns {operator_id|None, country|None, basis, limitation}.
    Only NG prefixes resolve; every other market returns UNKNOWN with
    an explicit reason — ranges are never invented.
    """
    normalized = normalize_e164(e164)
    country = country_for_e164(normalized)
    if country is None:
        return {"operator_id": None, "country": None,
                "basis": "unsupported-calling-code",
                "limitation": "calling code not in registry"}
    if country != "NG":
        return {"operator_id": None, "country": country,
                "basis": "ranges-unavailable-or-pooled",
                "limitation": ("no allocation ranges for %s; number "
                               "allocation is UNKNOWN" % country)}
    national = "0" + normalized[len("+234"):]
    prefix = national[:4]
    for op in OPERATORS:
        if op["country"] == "NG" and prefix in op["number_ranges"]:
            return {"operator_id": op["operator_id"], "country": "NG",
                    "basis": "ncc-allocation-prefix:" + prefix,
                    "limitation": ("allocation range only; MNP "
                                   "portability may change the current "
                                   "operator")}
    return {"operator_id": None, "country": "NG",
            "basis": "prefix-not-in-registry",
            "limitation": "prefix %s not allocated to a known NG "
                          "operator" % prefix}

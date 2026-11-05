"""Industry solution registry (Level 14 §6).

Single source of truth for the 45 industry modules: stable IDs,
display names, implementation status, and which shared platform
capabilities each module reuses. Statuses use the directive's
explicit vocabulary; nothing here claims implementation — every
module starts NOT_STARTED and moves only with evidence.
"""
from __future__ import annotations

from typing import Any

STATUSES = ("NOT_STARTED", "DISCOVERY", "DESIGNED", "IN_DEVELOPMENT",
            "TESTING", "PILOT", "OPERATIONAL", "VERIFIED")

# Shared platform capabilities a module may reuse (see domain map).
TXN = "transaction-monitoring"
RISK = "risk-scoring"
GRAPH = "graph-intelligence"
CASE = "case-management"
EVID = "evidence-management"
AI = "ai-explanation"
ALL_SHARED = (TXN, RISK, GRAPH, CASE, EVID, AI)

_ENTRIES: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("banking", "Banking", ALL_SHARED, "core vertical; generic engine applies"),
    ("fintech-payments", "Fintech & Digital Payments", ALL_SHARED, "core vertical; generic engine applies"),
    ("capital-markets", "Capital Markets & Investment", (TXN, RISK, GRAPH, CASE, EVID, AI), "needs market-data connectors"),
    ("insurance-pensions", "Insurance & Pensions", (RISK, GRAPH, CASE, EVID, AI), "needs actuarial/claims data model"),
    ("crypto-assets", "Cryptocurrency & Digital Assets", (TXN, GRAPH, RISK, CASE, EVID, AI), "needs chain-data connectors"),
    ("fx-remittance", "Foreign Exchange & Remittance", ALL_SHARED, "needs corridor/FX-rate data"),
    ("government", "Government & Public Administration", (CASE, EVID, AI), "needs classification/handling controls"),
    ("tax-revenue", "Tax & Revenue Authorities", (TXN, RISK, CASE, EVID, AI), "needs filing-system connectors"),
    ("law-enforcement", "Law Enforcement & Financial Intelligence", (GRAPH, CASE, EVID, AI), "needs FIU workflow + handling controls"),
    ("customs-border", "Customs & Border Administration", (TXN, RISK, CASE, EVID), "needs trade/customs data"),
    ("defence-security", "Defence & National Security", (GRAPH, CASE, EVID), "needs classification controls"),
    ("procurement-infra", "Public Procurement & Infrastructure", (TXN, RISK, CASE, EVID, AI), "needs tender/award data"),
    ("retail", "Retail & Supermarkets", (TXN, RISK, CASE), "needs POS/returns data model"),
    ("ecommerce", "E-commerce & Online Marketplaces", (TXN, RISK, GRAPH, CASE, AI), "needs marketplace/order data"),
    ("wholesale", "Wholesale & Distribution", (TXN, RISK, CASE), "needs B2B invoice data"),
    ("manufacturing", "Manufacturing & Industrial Production", (TXN, RISK, CASE, EVID), "needs production/cost data"),
    ("supply-chain", "Supply Chain & Logistics", (TXN, GRAPH, RISK, CASE), "needs shipment/tracking data"),
    ("import-export", "Import & Export Businesses", (TXN, RISK, GRAPH, CASE, EVID), "needs trade-finance data"),
    ("real-estate", "Real Estate & Property", (TXN, RISK, GRAPH, CASE, EVID), "needs registry/valuation data"),
    ("construction", "Construction & Engineering", (TXN, RISK, CASE, EVID), "needs project/contract data"),
    ("mining-resources", "Mining & Natural Resources", (TXN, RISK, CASE, EVID), "needs extraction/royalty data"),
    ("oil-gas", "Oil & Gas", (TXN, RISK, CASE, EVID), "needs production/lifting data"),
    ("automotive", "Automotive & Vehicle Trade", (TXN, RISK, CASE), "needs vehicle-registry data"),
    ("luxury-goods", "Luxury Goods & Precious Metals", (TXN, RISK, GRAPH, CASE), "needs provenance/assay data"),
    ("healthcare", "Healthcare & Hospitals", (TXN, RISK, CASE, EVID), "needs claims data; confidentiality handling"),
    ("pharma-biotech", "Pharmaceuticals & Biotechnology", (TXN, RISK, CASE, EVID), "needs trial/grant data"),
    ("education", "Education & Universities", (TXN, CASE), "needs grant/enrollment data"),
    ("legal", "Legal Services", (CASE, EVID), "privilege/confidentiality handling required"),
    ("accounting", "Accounting & Auditing", (TXN, RISK, CASE, EVID, AI), "needs ledger/audit data"),
    ("consulting", "Consulting & Professional Services", (TXN, CASE), "needs engagement/billing data"),
    ("telecom", "Telecommunications", (TXN, GRAPH, RISK, CASE), "needs CDR/subscriber data (lawful access)"),
    ("technology", "Technology & Software Companies", (TXN, RISK, CASE), "needs SaaS-billing data"),
    ("gaming-esports", "Gaming & Esports", (TXN, RISK, CASE), "needs virtual-economy data"),
    ("gambling", "Gambling & Casinos", (TXN, RISK, GRAPH, CASE, EVID), "needs wagering/payout data"),
    ("media", "Media, Advertising & Entertainment", (TXN, CASE), "needs royalty/ad-spend data"),
    ("social-platforms", "Social Media & Digital Platforms", (GRAPH, CASE), "needs platform-abuse signals"),
    ("agriculture", "Agriculture & Agribusiness", (TXN, RISK, CASE), "needs subsidy/yield data"),
    ("energy-utilities", "Energy & Utilities", (TXN, RISK, CASE), "needs metering/billing data"),
    ("aviation", "Aviation & Aerospace", (TXN, CASE, EVID), "needs manifest/charter data"),
    ("maritime", "Maritime & Shipping", (TXN, GRAPH, RISK, CASE, EVID), "needs AIS/manifest data"),
    ("transport", "Transportation & Mobility", (TXN, CASE), "needs fleet/fare data"),
    ("ngo", "NGOs & Humanitarian Organisations", (TXN, RISK, CASE, EVID), "needs grant/disbursement data"),
    ("charities", "Charities & Foundations", (TXN, RISK, CASE, EVID), "needs donation/endowment data"),
    ("hospitality", "Hotels & Hospitality", (TXN, CASE), "needs booking/folio data"),
    ("environmental", "Environmental & Waste Management", (TXN, CASE), "needs permit/manifest data"),
)


def registry() -> list[dict[str, Any]]:
    """Full module list. Status advances only with evidence."""
    items = []
    for ident, name, shared, note in _ENTRIES:
        status, evidence = _STATUS.get(ident, ("NOT_STARTED", ""))
        row = {"id": ident, "name": name, "status": status,
               "shared_reuse": list(shared), "note": note}
        if evidence:
            row["status_evidence"] = evidence
        items.append(row)
    return items


def get_module(ident: str) -> dict[str, Any] | None:
    for entry in registry():
        if entry["id"] == ident:
            return entry
    return None


# -- module profiles + status machine (slice-5) ------------------------
_PROFILES: dict[str, dict[str, Any]] = {}
_STATUS: dict[str, tuple[str, str]] = {}

PROFILE_KEYS = ("risk_taxonomy", "threat_scenarios", "detection_rules",
                "data_requirements", "workflows", "reports",
                "permissions", "compliance")

_TRANSITIONS = {
    "NOT_STARTED": ("DISCOVERY",),
    "DISCOVERY": ("DESIGNED",),
    "DESIGNED": ("IN_DEVELOPMENT",),
    "IN_DEVELOPMENT": ("TESTING",),
    "TESTING": ("PILOT", "IN_DEVELOPMENT"),
    "PILOT": ("OPERATIONAL", "TESTING"),
    "OPERATIONAL": ("VERIFIED", "PILOT"),
    "VERIFIED": (),
}


def register_profile(ident: str, profile: dict[str, Any]) -> None:
    """Attach a validated industry profile. Raises on bad shape."""
    if get_module(ident) is None:
        raise ValueError(f"INDUSTRY_UNKNOWN: {ident}")
    missing = [k for k in PROFILE_KEYS if k not in profile]
    if missing or profile.get("id") != ident:
        raise ValueError(f"INDUSTRY_PROFILE_INVALID: {ident} "
                         f"missing={missing}")
    _PROFILES[ident] = profile
    _STATUS.setdefault(ident, ("DESIGNED", "profile registered"))


def get_profile(ident: str) -> dict[str, Any] | None:
    return _PROFILES.get(ident)


def module_status(ident: str) -> tuple[str, str]:
    return _STATUS.get(ident, ("NOT_STARTED", ""))


def set_status(ident: str, status: str, evidence: str) -> None:
    """Advance a module's status along legal transitions with evidence."""
    if status not in STATUSES:
        raise ValueError(f"INDUSTRY_STATUS_UNKNOWN: {status}")
    if get_module(ident) is None:
        raise ValueError(f"INDUSTRY_UNKNOWN: {ident}")
    current, _ = module_status(ident)
    if status != current and status not in _TRANSITIONS[current]:
        raise ValueError(f"INDUSTRY_TRANSITION_ILLEGAL: {current} -> "
                         f"{status}")
    if not evidence or not evidence.strip():
        raise ValueError("INDUSTRY_EVIDENCE_REQUIRED")
    _STATUS[ident] = (status, evidence.strip())
    for entry in registry():
        if entry["id"] == ident:
            entry["status"] = status
            entry["status_evidence"] = _STATUS[ident][1]
            return entry
    return None

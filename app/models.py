"""Pydantic contracts for the CruiseShield hackathon vertical slice."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Channel(str, Enum):
    POS = "POS"
    ATM = "ATM"
    USSD = "USSD"
    MOBILE_APP = "MOBILE_APP"
    WEB = "WEB"
    CARD = "CARD"
    TRANSFER_NIP = "TRANSFER_NIP"
    QR = "QR"
    AGENT_AGENCY = "AGENT_AGENCY"
    API_OPEN_BANKING = "API_OPEN_BANKING"
    WALLET = "WALLET"
    MERCHANT = "MERCHANT"
    UNKNOWN = "UNKNOWN"


CHANNEL_ALIASES = {
    "point_of_sale": "POS",
    "app": "MOBILE_APP",
    "mobile": "MOBILE_APP",
    "mobile_app": "MOBILE_APP",
    "internet_banking": "WEB",
    "transfer": "TRANSFER_NIP",
    "nip": "TRANSFER_NIP",
    "agent": "AGENT_AGENCY",
    "agency": "AGENT_AGENCY",
    "api": "API_OPEN_BANKING",
    "open_banking": "API_OPEN_BANKING",
}


class Transaction(BaseModel):
    transaction_id: str
    amount_minor: int
    currency: str = "NGN"
    channel: Channel
    sender_account_id: str
    receiver_account_id: str
    occurred_at: str
    device_id: Optional[str] = None
    phone_id: Optional[str] = None
    ip_id: Optional[str] = None
    location_id: Optional[str] = None
    merchant_id: Optional[str] = None


class Event(BaseModel):
    event_id: str
    event_type: str = "financial.transaction.created"
    schema_version: str = "1.0"
    occurred_at: str
    source: str = "synthetic_demo"
    trace_id: str
    privacy_classification: str = "synthetic"
    transaction: Transaction
    entities: dict[str, Optional[str]] = Field(default_factory=dict)


class GraphNode(BaseModel):
    node_id: str
    node_type: str
    display_label: str
    synthetic_flag: bool = True
    source_record_ids: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    source_event_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    synthetic_flag: bool = True
    trace_id: str = ""


class RuleDefinition(BaseModel):
    rule_id: str
    rule_version: str
    description: str
    threshold: str
    severity: str
    weight: int
    enabled: bool = True


class RuleResult(BaseModel):
    rule_result_id: str
    rule_id: str
    rule_version: str
    triggered: bool
    observed_values: dict[str, Any] = Field(default_factory=dict)
    threshold: str = ""
    explanation: str = ""
    source_record_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    trace_id: str = ""


class RiskContribution(BaseModel):
    rule_id: str
    weight: int
    triggered: bool


class RiskAssessment(BaseModel):
    risk_assessment_id: str
    target_id: str
    target_type: str
    score: int
    band: str
    score_version: str
    contributions: list[RiskContribution] = Field(default_factory=list)
    rule_results: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    computed_at: str
    trace_id: str = ""
    limitations: str = ""


class EvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: str
    title: str
    description: str = ""
    source_record_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list)
    graph_edge_ids: list[str] = Field(default_factory=list)
    rule_result_ids: list[str] = Field(default_factory=list)
    observed_at: str = ""
    trace_id: str = ""
    synthetic_flag: bool = True
    evidence_version: str = "1.0"


class EvidencePackage(BaseModel):
    package_id: str
    scenario_id: str
    scenario_version: str
    trace_id: str
    items: list[EvidenceItem] = Field(default_factory=list)
    package_hash: str = ""
    evidence_version: str = "1.0"


class Alert(BaseModel):
    alert_id: str
    transaction_id: str
    title: str
    status: str = "OPEN"
    risk_assessment_id: str = ""
    created_at: str = ""
    trace_id: str = ""


class Investigation(BaseModel):
    investigation_id: str
    alert_id: str
    transaction_id: str
    status: str = "OPEN"
    created_at: str = ""
    trace_id: str = ""


class AgentRun(BaseModel):
    agent_run_id: str
    provider: str = "meta"
    model_id: str = ""
    prompt_version: str = "cs-prompt-v2"
    request_id: str = ""
    trace_id: str = ""
    evidence_package_id: str = ""
    evidence_ids_sent: list[str] = Field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    latency_ms: int = 0
    status: str = "PENDING"
    response_reference: str = ""
    schema_validation_status: str = "NOT_VALIDATED"
    evidence_reference_validation_status: str = "NOT_VALIDATED"
    error_code: str = ""
    synthetic_data_flag: bool = True
    result: dict[str, Any] = Field(default_factory=dict)


class Case(BaseModel):
    case_id: str
    investigation_id: str
    status: str = "NEW"
    created_at: str = ""
    updated_at: str = ""
    trace_id: str = ""


class HumanDecision(BaseModel):
    decision_id: str
    case_id: str
    actor_id: str
    actor_role: str = "INVESTIGATOR"
    decision: str = ""
    reason: str = ""
    evidence_viewed: list[str] = Field(default_factory=list)
    recommendation_at_decision: str = ""
    created_at: str = ""
    authorization_scope: str = "demo"
    trace_id: str = ""


class AuditEvent(BaseModel):
    audit_event_id: str
    actor_type: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    previous_state_reference: str = ""
    new_state_reference: str = ""
    reason: str = ""
    timestamp: str = ""
    trace_id: str = ""
    request_id: str = ""


class SimulationRun(BaseModel):
    simulation_id: str
    scenario_id: str
    target_transaction_id: str
    ignored_edge_ids: list[str] = Field(default_factory=list)
    assumption: str = ""
    baseline_score: int = 0
    simulated_score: int = 0
    baseline_band: str = ""
    simulated_band: str = ""
    limitations: str = ""
    created_at: str = ""
    trace_id: str = ""


class ScenarioManifest(BaseModel):
    scenario_id: str
    scenario_version: str
    title: str
    purpose: str
    seed_hash: str
    synthetic_notice: str = "Synthetic demo data."
    event_sequence: list[str] = Field(default_factory=list)
    expected_rule_results: dict[str, bool] = Field(default_factory=dict)
    expected_graph_counts: dict[str, int] = Field(default_factory=dict)
    expected_risk_band: dict[str, str] = Field(default_factory=dict)
    expected_evidence_ids: list[str] = Field(default_factory=list)

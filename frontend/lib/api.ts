/* Typed client for the existing CruiseShield FastAPI backend.
 * Reads only the real JSON contracts (see docs/COMMAND_EXPERIENCE/01-AUDIT.md).
 * No secrets here: NEXT_PUBLIC_API_BASE_URL is a public base URL, and the
 * browser never handles MODEL_API_KEY (backend-only, server side). */

export interface HealthCheck {
  status: string;
  version: string;
  scenario_id: string;
  run_id: string;
  checks: Record<string, string>;
}

interface ApiErrorBody {
  error?: { code?: string; message?: string; trace_id?: string };
}

export class ApiError extends Error {
  code: string;
  status: number;
  traceId: string;

  constructor(code: string, message: string, status: number, traceId: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.traceId = traceId;
  }
}

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

async function requestJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, {
      signal,
      cache: "no-store",
      credentials: "include",
    });
  } catch (err: unknown) {
    throw new ApiError(
      "BACKEND_UNREACHABLE",
      err instanceof Error ? err.message : "backend unreachable",
      0,
      ""
    );
  }
  const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
  if (!res.ok) {
    throw new ApiError(
      data.error?.code ?? `HTTP_${res.status}`,
      data.error?.message ?? "request failed",
      res.status,
      data.error?.trace_id ?? ""
    );
  }
  return data as T;
}

export function getHealth(signal?: AbortSignal): Promise<HealthCheck> {
  return requestJson<HealthCheck>("/api/v1/health", signal);
}

export interface Transaction {
  transaction_id: string;
  amount_minor: number;
  currency: string;
  channel: string;
  sender_account_id: string;
  receiver_account_id: string;
  occurred_at: string;
}

export interface RuleResult {
  rule_result_id: string;
  rule_id: string;
  rule_version: string;
  triggered: boolean;
  threshold: string;
  explanation: string;
  source_record_ids: string[];
  evidence_ids: string[];
  trace_id: string;
}

export interface RiskAssessment {
  risk_assessment_id: string;
  target_id: string;
  target_type: string;
  score: number;
  band: string;
  score_version: string;
  computed_at: string;
  limitations: string;
}

export interface InvestigationSummary {
  investigation_id: string;
  alert_id: string;
  transaction_id: string;
  status: string;
}

export interface InvestigationDetail {
  investigation: InvestigationSummary;
  alert: { alert_id: string; title: string; status: string };
  transaction: Transaction;
  risk_transaction: RiskAssessment;
  risk_network: RiskAssessment;
  rule_results: RuleResult[];
  case: { case_id: string; status: string } | null;
  evidence_package_id: string;
  evidence_count: number;
}

export interface EvidenceItem {
  evidence_id: string;
  evidence_type: string;
  title: string;
  description: string;
  event_ids: string[];
  graph_edge_ids: string[];
  rule_result_ids: string[];
}

export interface EvidencePackage {
  package_id: string;
  scenario_id: string;
  package_hash: string;
  items: EvidenceItem[];
}

export interface KeyFinding {
  finding: string;
  evidence_ids: string[];
  confidence_label: string;
  caveat: string;
}

export interface AiResult {
  summary: string;
  key_findings: KeyFinding[];
  alternative_explanations: string[];
  missing_information: string[];
  conclusion: string;
  disclaimer: string;
}

export interface AgentRun {
  agent_run_id: string;
  model_id: string;
  prompt_version: string;
  request_id: string;
  latency_ms: number;
  status: string;
  schema_validation_status: string;
  evidence_reference_validation_status: string;
  error_code: string;
  result: AiResult;
}

async function postJson<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal
): Promise<T> {
  // Phase 5: credentialed POSTs carry the HttpOnly session cookie
  // (Vercel -> Render) and the X-Requested-With CSRF header the backend
  // requires for cookie-authed POSTs. Harmless when auth is disabled.
  const init: RequestInit = {
    method: "POST",
    signal,
    credentials: "include",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  };
  if (body !== undefined) {
    init.headers = {
      ...(init.headers as Record<string, string>),
      "Content-Type": "application/json",
    };
    init.body = JSON.stringify(body);
  }
  // Gap-closure (D-002): shared demo write token for hosted backends.
  // Unset locally → header omitted, behavior unchanged. When set it is a
  // PUBLIC shared-demo credential (baked into client chunks by Next.js) —
  // appropriate for staging demos, never user authentication.
  const writeToken = process.env.NEXT_PUBLIC_DEMO_WRITE_TOKEN ?? "";
  if (writeToken !== "") {
    init.headers = {
      ...(init.headers as Record<string, string> | undefined),
      Authorization: `Bearer ${writeToken}`,
    };
  }
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, init);
  } catch (err: unknown) {
    throw new ApiError(
      "BACKEND_UNREACHABLE",
      err instanceof Error ? err.message : "backend unreachable",
      0,
      ""
    );
  }
  const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
  if (!res.ok) {
    throw new ApiError(
      data.error?.code ?? `HTTP_${res.status}`,
      data.error?.message ?? "request failed",
      res.status,
      data.error?.trace_id ?? ""
    );
  }
  return data as T;
}

export function getInvestigation(
  invId: string,
  signal?: AbortSignal
): Promise<InvestigationDetail> {
  return requestJson<InvestigationDetail>(
    `/api/v1/investigations/${encodeURIComponent(invId)}`,
    signal
  );
}

export function getEvidencePackage(
  invId: string,
  signal?: AbortSignal
): Promise<EvidencePackage> {
  return requestJson<EvidencePackage>(
    `/api/v1/investigations/${encodeURIComponent(invId)}/evidence-package`,
    signal
  );
}

export function postAiAnalysis(
  invId: string,
  signal?: AbortSignal
): Promise<AgentRun> {
  return postJson<AgentRun>(
    `/api/v1/investigations/${encodeURIComponent(invId)}/ai-analysis`,
    undefined,
    signal
  );
}

export function postAiFollowup(
  invId: string,
  question: string,
  signal?: AbortSignal
): Promise<AgentRun> {
  return postJson<AgentRun>(
    `/api/v1/investigations/${encodeURIComponent(invId)}/ai-followup`,
    { question },
    signal
  );
}

/* Batch 3: graph explorer. Field names mirror app/seed.py node/edge dicts
 * exactly; GET /api/v1/graph/{txn} returns the full seeded graph. */

export interface GraphNode {
  node_id: string;
  node_type: string;
  display_label: string;
  synthetic_flag: boolean;
  source_record_ids: string[];
}

export interface GraphEdge {
  edge_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  source_event_ids: string[];
  evidence_ids: string[];
  valid_from: string;
  valid_to: string | null;
  synthetic_flag: boolean;
  trace_id: string;
}

export interface GraphResponse {
  transaction_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  provenance_errors: string[];
  counts: { nodes: number; edges: number };
}

export function getGraph(
  txnId: string,
  signal?: AbortSignal
): Promise<GraphResponse> {
  return requestJson<GraphResponse>(
    `/api/v1/graph/${encodeURIComponent(txnId)}`,
    signal
  );
}

/* DI-07: derived intel overlay. Nodes conform to GraphNode so the
 * explorers render them with zero renderer changes; unavailable
 * categories carry honest reasons instead of fabricated nodes. */

export interface OverlayDeviceDetail {
  node_id: string;
  node_type: string;
  status: string;
  identity_status: string;
  first_seen: string;
  last_seen: string;
  linked_accounts: number;
  linked_transactions: number;
  account_ids: string[];
  attributes: Record<string, string>;
  attributes_source: string;
  evidence_refs: { graph_edge_ids: string[]; event_ids: string[] };
  synthetic: boolean;
  derived: boolean;
}

export interface OverlayResponse {
  transaction_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_details: Record<string, OverlayDeviceDetail>;
  unavailable: Record<string, string>;
  counts: {
    overlay_nodes: number;
    overlay_edges: number;
    base_nodes: number;
    base_edges: number;
  };
  derived: boolean;
  synthetic: boolean;
}

export function getGraphOverlay(
  txnId: string,
  signal?: AbortSignal
): Promise<OverlayResponse> {
  return requestJson<OverlayResponse>(
    `/api/v1/graph/${encodeURIComponent(txnId)}/overlay`,
    signal
  );
}

/* DI-10: device/IP/geo intelligence clients. Shapes mirror
 * app/device_intel.py, app/ip_intel.py, app/geo_intel.py,
 * app/intel_link.py, app/intel_evidence.py, app/risk_intel.py. */

export interface DeviceProfile {
  device_id: string;
  identity_status: string;
  disclaimer: string;
  first_seen: string;
  last_seen: string;
  account_ids: string[];
  txn_ids: string[];
  observation_count: number;
  shared: boolean;
  attributes: Record<string, string> | null;
  attributes_source: string;
  observations: {
    obs_id: string;
    device_id: string;
    account_id: string | null;
    txn_id: string | null;
    observed_at: string;
    source: string;
    source_ref: string;
    synthetic: boolean;
  }[];
  evidence_refs: { graph_edge_ids: string[]; event_ids: string[] };
}

export function getDevice(
  deviceId: string,
  signal?: AbortSignal
): Promise<DeviceProfile> {
  return requestJson<DeviceProfile>(
    `/api/v1/devices/${encodeURIComponent(deviceId)}`,
    signal
  );
}

export interface IpObservationList {
  ip_label: string;
  address_status: string;
  observations: {
    obs_id: string;
    ip_label: string;
    address: string | null;
    address_status: string;
    account_id: string | null;
    txn_id: string | null;
    observed_at: string;
    source: string;
    source_ref: string;
    synthetic: boolean;
  }[];
}

export function getIpObservations(
  label: string,
  signal?: AbortSignal
): Promise<IpObservationList> {
  return requestJson<IpObservationList>(
    `/api/v1/ip-observations/${encodeURIComponent(label)}`,
    signal
  );
}

export interface GeoObservationResult {
  identifier: string;
  kind: string;
  observations?: {
    obs_id: string;
    location_label: string;
    geo_status: string;
    reason: string;
    account_id: string | null;
    txn_id: string | null;
    observed_at: string;
    source_ref: string;
    synthetic: boolean;
  }[];
  lookup?: {
    status: string;
    reason: string;
    country_code: string;
    city: string;
    confidence: string;
    approximate_only: boolean;
  };
}

export function getGeoObservations(
  identifier: string,
  signal?: AbortSignal
): Promise<GeoObservationResult> {
  return requestJson<GeoObservationResult>(
    `/api/v1/geo-observations/${encodeURIComponent(identifier)}`,
    signal
  );
}

export interface TxnIntel {
  transaction_id: string;
  source_account_id: string;
  destination_account_id: string;
  transaction_time: string;
  device_observations: DeviceProfile["observations"];
  ip_observations: IpObservationList["observations"];
  geolocation_observations: NonNullable<GeoObservationResult["observations"]>;
  device_graph_refs: Record<string, string[]>;
  observation_first_seen: string;
  observation_last_seen: string;
  provenance: { event_ids: string[] };
  synthetic: boolean;
  limitations: string[];
}

export function getTransactionIntel(
  txnId: string,
  signal?: AbortSignal
): Promise<TxnIntel> {
  return requestJson<TxnIntel>(
    `/api/v1/transactions/${encodeURIComponent(txnId)}/intel`,
    signal
  );
}

export interface InvIntel {
  investigation_id: string;
  transaction_id: string;
  transaction_intel: TxnIntel | { status: string };
  isolation: string;
  synthetic: boolean;
  limitations: string[];
}

export function getInvestigationIntel(
  invId: string,
  signal?: AbortSignal
): Promise<InvIntel> {
  return requestJson<InvIntel>(
    `/api/v1/investigations/${encodeURIComponent(invId)}/intel`,
    signal
  );
}

export interface IntelFinding {
  finding_id: string;
  category: string;
  signal_id: string;
  status: string;
  subject_type: string;
  subject_ref: string;
  transaction_ref: string;
  account_ref: string;
  investigation_ref: string;
  source_observation_ids: string[];
  source_event_ids: string[];
  source_edge_ids: string[];
  observed_at: string;
  processed_at: string;
  evidence_refs: string[];
  provenance: string;
  confidence: string;
  freshness: string;
  synthetic: boolean;
  derivation_method: string;
  explanation: string;
  limitations: string[];
  human_review: string;
}

export interface IntelEvidence {
  investigation_id: string;
  findings: IntelFinding[];
  // Flag-OFF shape mirrors RiskIntelResult: findings empty, trace absent.
  enabled?: boolean;
  status?: string;
  detail?: string;
  engine?: string;
  trace?: {
    investigation_id: string;
    transaction_id: string;
    findings: {
      finding_id: string;
      signal_id: string;
      source_observation_ids: string[];
      evidence_refs: string[];
      provenance: string;
    }[];
    synthetic: boolean;
  } | null;
  synthetic?: boolean;
}

export function getIntelEvidence(
  invId: string,
  signal?: AbortSignal
): Promise<IntelEvidence> {
  return requestJson<IntelEvidence>(
    `/api/v1/investigations/${encodeURIComponent(invId)}/intel-evidence`,
    signal
  );
}

export interface RiskIntelResult {
  engine: string;
  enabled: boolean;
  status?: string;
  detail?: string;
  subject?: { type: string; id: string };
  finding_count?: number;
  numeric_score?: number | null;
  score_note?: string;
  authoritative_engine?: string;
}

export function getRiskIntel(
  identifier: string,
  signal?: AbortSignal
): Promise<RiskIntelResult> {
  return requestJson<RiskIntelResult>(
    `/api/v1/risk-intelligence/${encodeURIComponent(identifier)}`,
    signal
  );
}

/* Batch 4: replay, simulation, cases, audit, demo. Shapes mirror
 * app/replay.py, app/simulate.py, app/cases.py, app/store.py. */

export interface ReplayEvent {
  event_id: string;
  event_type: string;
  occurred_at: string;
  source: string;
  trace_id: string;
  transaction: Transaction;
  entities: Record<string, string | null>;
}

export interface ReplayState {
  scenario_id: string;
  cursor: number;
  total: number;
  current_event: ReplayEvent | null;
  cumulative_event_ids: string[];
  cumulative_transaction_ids: string[];
  cumulative_edge_ids: string[];
  counts: { events: number; transactions: number; edges: number };
}

export interface SimulationResult {
  simulation_id: string;
  scenario_id: string;
  target_transaction_id: string;
  ignored_edge_ids: string[];
  assumption: string;
  baseline_score: number;
  simulated_score: number;
  baseline_band: string;
  simulated_band: string;
  limitations: string;
  created_at: string;
  trace_id: string;
}

export interface RiskResponse {
  assessment: RiskAssessment;
  rule_results: RuleResult[];
}

export interface CaseRecord {
  case_id: string;
  investigation_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  trace_id: string;
}

export interface DecisionRecord {
  decision_id: string;
  case_id: string;
  actor_id: string;
  actor_role: string;
  decision: string;
  reason: string;
  evidence_viewed: string[];
  recommendation_at_decision: string;
  created_at: string;
  authorization_scope: string;
  trace_id: string;
}

export interface AiAssessmentFinding {
  finding: string;
  confidence_label: string;
  evidence_ids: string[];
}

export interface AiAssessment {
  agent_run_id: string;
  model_id: string;
  status: string;
  prompt_version: string;
  conclusion: string;
  missing_information: string[];
  key_findings: AiAssessmentFinding[];
  schema_validation_status: string;
  evidence_reference_validation_status: string;
  latency_ms: number;
  completed_at: string;
}

export interface CaseDetail {
  case: CaseRecord;
  decisions: DecisionRecord[];
  allowed_transitions: string[];
  latest_ai_run: AiAssessment | null;
}

export interface DecisionInput {
  decision: string;
  target_status: string;
  reason: string;
  actor_id: string;
  evidence_viewed: string[];
  recommendation: string;
}

export interface DecisionResponse {
  decision: DecisionRecord;
  audit: AuditEntry;
  case: CaseRecord;
}

export interface AuditEntry {
  audit_event_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  target_type: string;
  target_id: string;
  previous_state_reference: string;
  new_state_reference: string;
  reason: string;
  timestamp: string;
  trace_id: string;
  request_id: string;
}

export interface DemoScenario {
  scenario_id: string;
  title: string;
}

export interface DemoScenarioList {
  scenarios: DemoScenario[];
  active_scenario_id: string;
}

export interface DemoResetResult {
  scenario_id: string;
  run_id: string;
  trace_id: string;
  seed_hash: string;
  manifest: Record<string, unknown>;
}

export function getReplay(
  scenarioId: string,
  cursor: number,
  signal?: AbortSignal
): Promise<ReplayState> {
  return requestJson<ReplayState>(
    `/api/v1/replay/${encodeURIComponent(scenarioId)}?cursor=${cursor}`,
    signal
  );
}

export function getRisk(
  txnId: string,
  scope: string,
  signal?: AbortSignal
): Promise<RiskResponse> {
  return requestJson<RiskResponse>(
    `/api/v1/risk/${encodeURIComponent(txnId)}?scope=${encodeURIComponent(scope)}`,
    signal
  );
}

export function postSimulation(
  targetTransactionId: string,
  ignoredEdgeIds: string[],
  assumption: string,
  signal?: AbortSignal
): Promise<SimulationResult> {
  return postJson<SimulationResult>(
    "/api/v1/simulations",
    {
      target_transaction_id: targetTransactionId,
      ignored_edge_ids: ignoredEdgeIds,
      assumption,
      actor_id: "investigator",
    },
    signal
  );
}

export function getCase(
  caseId: string,
  signal?: AbortSignal
): Promise<CaseDetail> {
  return requestJson<CaseDetail>(
    `/api/v1/cases/${encodeURIComponent(caseId)}`,
    signal
  );
}

export function postDecision(
  caseId: string,
  input: DecisionInput,
  signal?: AbortSignal
): Promise<DecisionResponse> {
  return postJson<DecisionResponse>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/decisions`,
    {
      decision: input.decision,
      target_status: input.target_status,
      reason: input.reason,
      actor_id: input.actor_id,
      evidence_viewed: input.evidence_viewed,
      recommendation: input.recommendation,
    },
    signal
  );
}

export function getCaseAudit(
  caseId: string,
  signal?: AbortSignal
): Promise<{ audits: AuditEntry[] }> {
  return requestJson<{ audits: AuditEntry[] }>(
    `/api/v1/cases/${encodeURIComponent(caseId)}/audit`,
    signal
  );
}

/* Alerts feed (notification bell). Field names mirror app/store.py and
 * app/models.py Alert exactly. */

export interface AlertItem {
  alert_id: string;
  transaction_id: string;
  title: string;
  status: string;
  risk_assessment_id: string;
  created_at: string;
  trace_id: string;
}

export function listAlerts(signal?: AbortSignal): Promise<{
  alerts: AlertItem[];
}> {
  return requestJson<{ alerts: AlertItem[] }>("/api/v1/alerts", signal);
}

export function listScenarios(signal?: AbortSignal): Promise<DemoScenarioList> {
  return requestJson<DemoScenarioList>("/api/v1/demo/scenarios", signal);
}

export function resetDemo(
  scenarioId: string,
  signal?: AbortSignal
): Promise<DemoResetResult> {
  return postJson<DemoResetResult>(
    "/api/v1/demo/reset",
    { scenario_id: scenarioId },
    signal
  );
}

/* Phase 5: protected-demo login. Open demo (auth_enabled false) behaves
 * exactly as before; staging gates every data endpoint behind the
 * HttpOnly session cookie set by postLogin. */

export interface AuthMode {
  auth_enabled: boolean;
}

export interface AuthSession {
  user: string;
  role: string;
}

export function getAuthMode(signal?: AbortSignal): Promise<AuthMode> {
  return requestJson<AuthMode>("/api/v1/auth/mode", signal);
}

export function getAuthMe(signal?: AbortSignal): Promise<AuthSession> {
  return requestJson<AuthSession>("/api/v1/auth/me", signal);
}

export function postLogin(
  username: string,
  password: string,
  signal?: AbortSignal
): Promise<AuthSession> {
  return postJson<AuthSession>(
    "/api/v1/auth/login",
    { username, password },
    signal
  );
}

export function postLogout(signal?: AbortSignal): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>("/api/v1/auth/logout", undefined, signal);
}

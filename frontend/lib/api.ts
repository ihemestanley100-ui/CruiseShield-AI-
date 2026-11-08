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

/* User-worded failure text. Raw API codes and English server detail
 * never reach the UI: every failure maps to a translated `common`
 * string by class (permission / unreachable / load / unknown).
 * Pass the common-namespace translator from the rendering component.
 * Server detail stays in the console/network log for debugging. */
export function userErrorMessage(
  err: unknown,
  t: (key: string) => string
): string {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) return t("notPermitted");
    if (err.code === "REQUEST_TIMEOUT") return t("timedOut");
    if (err.status === 503) return t("unavailable");
    if (err.code === "BACKEND_UNREACHABLE" || err.status === 0)
      return t("unreachable");
    return t("loadFailed");
  }
  if (err instanceof Error) return t("loadFailed");
  return t("requestFailed");
}

/* J3-P6: session-expiry signal. Any 401/403 from a data endpoint means
 * the session is gone (or never existed): the login gate listens and
 * re-checks /me, flipping the whole app back to sign-in so an expired
 * session can never strand a page on a bare error card. The whole auth
 * namespace is excluded: the gate consumes auth outcomes directly, and
 * signalling /me re-triggers recheck() forever (observed /me storm).
 * SSR-safe: no window on the server, no dispatch. */
export const UNAUTHORIZED_EVENT = "csai:unauthorized";

function notifyUnauthorized(path: string, status: number) {
  if (typeof window === "undefined") return;
  if (path.startsWith("/api/v1/auth/")) return;
  if (status !== 401 && status !== 403) return;
  window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
}

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

/** Client-side request deadline: a hung backend surfaces as a timeout
 * state with retry, never an eternal spinner. */
export const REQUEST_TIMEOUT_MS = 15000;

/* Combine the caller's cancellation signal with the request deadline.
 * Hand-rolled (no AbortSignal.any) so older browsers behave the same;
 * the timer is always cleared once the request settles. */
function deadline(signal?: AbortSignal): {
  signal: AbortSignal;
  clear: () => void;
} {
  const controller = new AbortController();
  const timer = setTimeout(() => {
    controller.abort(new DOMException("Request timed out", "TimeoutError"));
  }, REQUEST_TIMEOUT_MS);
  if (signal) {
    if (signal.aborted) {
      controller.abort(signal.reason);
    } else {
      signal.addEventListener(
        "abort",
        () => controller.abort(signal.reason),
        { once: true }
      );
    }
  }
  return { signal: controller.signal, clear: () => clearTimeout(timer) };
}

function toNetworkError(err: unknown): ApiError {
  // AbortError (caller cancelled) and TimeoutError (deadline fired)
  // both mean "no answer in time", distinct from offline/unreachable.
  // Match by name: real fetch rejections are DOMExceptions, which do
  // not inherit from Error.
  const shape = err as { name?: unknown; message?: unknown } | null;
  const timedOut = shape?.name === "AbortError" || shape?.name === "TimeoutError";
  const message =
    typeof shape?.message === "string" ? shape.message : "backend unreachable";
  return new ApiError(
    timedOut ? "REQUEST_TIMEOUT" : "BACKEND_UNREACHABLE",
    message,
    0,
    ""
  );
}

async function requestJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const gate = deadline(signal);
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, {
      signal: gate.signal,
      cache: "no-store",
      credentials: "include",
    });
  } catch (err: unknown) {
    throw toNetworkError(err);
  } finally {
    gate.clear();
  }
  const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
  if (!res.ok) {
    notifyUnauthorized(path, res.status);
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
  phone_id?: string | null;
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
  // R6: the public frontend ships WITHOUT the platform write token
  // (header omitted, writes use login sessions). If the variable is
  // ever set, the value bakes PUBLIC into client chunks — never user
  // authentication, never a copy of the backend secret.
  const writeToken = process.env.NEXT_PUBLIC_DEMO_WRITE_TOKEN ?? "";
  if (writeToken !== "") {
    init.headers = {
      ...(init.headers as Record<string, string> | undefined),
      Authorization: `Bearer ${writeToken}`,
    };
  }
  const gate = deadline(signal);
  init.signal = gate.signal;
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, init);
  } catch (err: unknown) {
    throw toNetworkError(err);
  } finally {
    gate.clear();
  }
  const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
  if (!res.ok) {
    notifyUnauthorized(path, res.status);
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

/* GAP-012: persisted AI run receipt. Shape mirrors the stored ai_runs
 * record (GET /api/v1/ai-runs/{id} returns it verbatim). */

export function getAiRun(
  runId: string,
  signal?: AbortSignal
): Promise<AgentRun> {
  return requestJson<AgentRun>(
    `/api/v1/ai-runs/${encodeURIComponent(runId)}`,
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

/* GAP-012: per-account intel summary. Shape mirrors
 * app/intel_link.py account_intel exactly. */

export interface SharedDeviceEntry {
  device_id: string;
  account_ids: string[];
  txn_ids: string[];
  graph_edge_ids: string[];
  event_ids: string[];
  identity_status: string;
  synthetic: boolean;
}

export interface SharedIpEntry {
  ip_label: string;
  address_status: string;
  account_ids: string[];
  txn_ids: string[];
  event_ids: string[];
  synthetic: boolean;
}

export interface AcctIntel {
  account_id: string;
  known_devices: string[];
  known_ip_labels: string[];
  known_geo_labels: string[];
  first_seen: string;
  last_seen: string;
  shared_devices: SharedDeviceEntry[];
  shared_ips: SharedIpEntry[];
  transaction_count: number;
  transaction_ids: string[];
  investigation_count: number;
  investigation_ids: string[];
  provenance: { event_ids: string[] };
  synthetic: boolean;
  limitations: string[];
}

export function getAccountIntel(
  accountId: string,
  signal?: AbortSignal
): Promise<AcctIntel> {
  return requestJson<AcctIntel>(
    `/api/v1/accounts/${encodeURIComponent(accountId)}/intel`,
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

/* Batch 4: replay, simulation, cases, audit, platform. Shapes mirror
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

export interface PlatformScenario {
  scenario_id: string;
  title: string;
}

export interface PlatformScenarioList {
  scenarios: PlatformScenario[];
  active_scenario_id: string;
}

export interface PlatformResetResult {
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

/* GAP-012: base transaction record plus both scored scopes.
 * Shape mirrors GET /api/v1/transactions/{id} exactly. */

export interface TransactionResponse {
  transaction: Transaction;
  risk_transaction: RiskAssessment;
  risk_network: RiskAssessment;
}

export function getTransaction(
  txnId: string,
  signal?: AbortSignal
): Promise<TransactionResponse> {
  return requestJson<TransactionResponse>(
    `/api/v1/transactions/${encodeURIComponent(txnId)}`,
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

/* Notification center (per-caller read state over alerts). Field
 * names mirror the /api/v1/notifications contract. */

export interface NotificationItem {
  notification_id: string;
  title: string;
  status: string;
  transaction_id: string | null;
  created_at: string;
  read: boolean;
}

export interface NotificationList {
  notifications: NotificationItem[];
  unread_count: number;
  synthetic_notice: string;
}

export function listNotifications(
  signal?: AbortSignal
): Promise<NotificationList> {
  return requestJson<NotificationList>("/api/v1/notifications", signal);
}

export function markNotificationsRead(
  body: { notification_ids?: string[]; all?: boolean },
  signal?: AbortSignal
): Promise<{ marked: string[]; unread_count: number }> {
  return postJson<{ marked: string[]; unread_count: number }>(
    "/api/v1/notifications/read",
    body,
    signal
  );
}

export function listScenarios(signal?: AbortSignal): Promise<PlatformScenarioList> {
  return requestJson<PlatformScenarioList>("/api/v1/platform/scenarios", signal);
}

export function resetWorkspace(
  scenarioId: string,
  signal?: AbortSignal
): Promise<PlatformResetResult> {
  return postJson<PlatformResetResult>(
    "/api/v1/platform/reset",
    { scenario_id: scenarioId },
    signal
  );
}

/* Phase 5: protected login. Open mode (auth_enabled false) behaves
 * exactly as before; staging gates every data endpoint behind the
 * HttpOnly session cookie set by postLogin. */

export interface AuthMode {
  auth_enabled: boolean;
}

export interface AuthSession {
  user: string;
  role: string;
  permissions: string[];
}

export function getAuthMode(signal?: AbortSignal): Promise<AuthMode> {
  return requestJson<AuthMode>("/api/v1/auth/mode", signal);
}

export function getAuthMe(signal?: AbortSignal): Promise<AuthSession> {
  return requestJson<AuthSession>("/api/v1/auth/me", signal);
}

export interface DetectorInfo {
  family: string;
  version: string;
  status: string;
  description: string;
  rules: string[];
}

export interface DetectorList {
  detectors: DetectorInfo[];
}

export interface SignalsSummary {
  total_signals: number;
  unique_transactions_flagged: number;
  unique_entities_flagged: number;
  unique_investigations_created?: number;
  false_positive_rate?: number | null;
  false_positive_basis?: string;
  by_family: Record<string, number>;
  by_severity: Record<string, number>;
  measurement_period: { start: string; end: string };
  generated_at: string;
  tenant_scope: string;
  evaluation: {
    transactions_evaluated: number;
    detector_version: string;
    latency_ms: number;
    unknown_location_txns: number;
    family_runs?: Record<string, number>;
    family_latency_ms?: Record<string, number>;
    family_errors?: { family: string; error: string }[];
    execution_id?: string;
    note: string;
  };
  note: string;
}

export interface ChannelRow {
  channel: string;
  transactions: number;
  unique_transactions: number;
  signals: number;
  unique_flagged: number;
  last_seen: string;
  integration: string;
  note: string;
}

export interface ChannelsSummary {
  channels: ChannelRow[];
  unmapped_raw_codes: string[];
  unmapped_alert: boolean;
  generated_at: string;
  tenant_scope: string;
}

export interface MatrixCell {
  family: string;
  channel: string;
  status: string;
  signals: number;
  transactions: number;
  evidence_signal_id: string;
}

export interface DetectionMatrix {
  cells: MatrixCell[];
  generated_at: string;
  tenant_scope: string;
}

export interface DetectionBundle {
  summary: SignalsSummary;
  channels: ChannelsSummary;
  detectors: DetectorList;
  matrix: DetectionMatrix;
  timeSeries?: SignalsTimeSeries;
}

export interface TimeBucket {
  bucket: string;
  signals: number;
  unique_txns: number;
}

export interface SignalsTimeSeries {
  granularity: string;
  buckets: TimeBucket[];
  total_signals: number;
  measurement_period: { start: string; end: string };
  generated_at: string;
  tenant_scope: string;
}

export interface SignalSearchRow extends Omit<SignalEvent, "outcome"> {
  outcome: string | null;
  linked_investigations: string[];
}

export interface SignalSearchPage {
  signals: SignalSearchRow[];
  total: number;
  limit: number;
  offset: number;
  tenant_scope: string;
}

export interface SignalDetail extends SignalEvent {
  outcome: {
    current: string;
    history: {
      outcome: string;
      actor: string;
      note: string;
      recorded_at: string;
    }[];
  } | null;
  link: {
    history: {
      investigation_id: string;
      actor: string;
      linked_at: string;
    }[];
  } | null;
  tenant_scope: string;
}

export function getDetectors(signal?: AbortSignal): Promise<DetectorList> {
  return requestJson<DetectorList>("/api/v1/detectors", signal);
}

export function getSignalsSummary(
  signal?: AbortSignal
): Promise<SignalsSummary> {
  return requestJson<SignalsSummary>("/api/v1/signals/summary", signal);
}

export function getChannelsSummary(
  signal?: AbortSignal
): Promise<ChannelsSummary> {
  return requestJson<ChannelsSummary>("/api/v1/channels/summary", signal);
}

export function getDetectionMatrix(
  signal?: AbortSignal
): Promise<DetectionMatrix> {
  return requestJson<DetectionMatrix>("/api/v1/detection/matrix", signal);
}

export interface SignalEvent {
  signal_id: string;
  detector_family: string;
  detector_version: string;
  rule_id: string;
  rule_version: string;
  transaction_id: string;
  channel: string;
  channel_canonical?: string;
  execution_id?: string;
  severity: string;
  occurred_at: string;
  tenant_id: string;
  entities: { sender: string; receiver: string };
  reason: string;
  evidence: Record<string, unknown>;
  outcome: string;
}

export interface TxnSignals {
  transaction_id: string;
  signals: SignalEvent[];
  signal_count: number;
  investigation: InvestigationSummary | null;
  case: { case_id: string; status: string } | null;
  audits: AuditEntry[];
  tenant_scope: string;
}

export function getSignalsTimeSeries(
  granularity: string = "day",
  signal?: AbortSignal
): Promise<SignalsTimeSeries> {
  return requestJson<SignalsTimeSeries>(
    `/api/v1/signals/time-series?granularity=${encodeURIComponent(
      granularity
    )}`,
    signal
  );
}

export function getSignalsSearch(
  params: {
    q?: string;
    family?: string;
    channel?: string;
    severity?: string;
    limit?: number;
    offset?: number;
  } = {},
  signal?: AbortSignal
): Promise<SignalSearchPage> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return requestJson<SignalSearchPage>(
    `/api/v1/signals/search${suffix}`,
    signal
  );
}

export function getSignalDetail(
  signalId: string,
  signal?: AbortSignal
): Promise<SignalDetail> {
  return requestJson<SignalDetail>(
    `/api/v1/signals/${encodeURIComponent(signalId)}`,
    signal
  );
}

export function postSignalOutcome(
  signalId: string,
  outcome: string,
  note: string = "",
  signal?: AbortSignal
): Promise<{ signal_id: string; outcome: string; recorded_at: string }> {
  return postJson<{ signal_id: string; outcome: string; recorded_at: string }>(
    `/api/v1/signals/${encodeURIComponent(signalId)}/outcome`,
    { outcome, note },
    signal
  );
}

export function postSignalLink(
  signalId: string,
  investigationId: string,
  signal?: AbortSignal
): Promise<{
  signal_id: string;
  investigation_id: string;
  linked_at: string;
}> {
  return postJson<{
    signal_id: string;
    investigation_id: string;
    linked_at: string;
  }>(
    `/api/v1/signals/${encodeURIComponent(signalId)}/link`,
    { investigation_id: investigationId },
    signal
  );
}

export function getTxnSignals(
  txnId: string,
  signal?: AbortSignal
): Promise<TxnSignals> {
  return requestJson<TxnSignals>(
    `/api/v1/signals/by-transaction/${encodeURIComponent(txnId)}`,
    signal
  );
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

export function postLogoutAll(
  signal?: AbortSignal
): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>(
    "/api/v1/auth/logout-all",
    undefined,
    signal
  );
}

/* Telecom Identity clients. Shapes mirror app/telecom_registry.py,
 * app/telecom_verify.py, app/telecom_providers.py. Subjects arrive
 * masked + hashed only; raw E.164 is never returned. */

export interface TelecomOperator {
  operator_id: string;
  country: string;
  country_name: string;
  name: string;
  aliases: string[];
  mcc_mnc: string[];
  number_ranges: string[];
  range_note: string;
  portability_support: boolean | "unknown";
  apis: Record<string, { status: string; note: string }>;
  coverage_status: string;
  provenance: {
    source: string;
    confidence: string;
    registry_version: string;
    updated: string;
  };
}

export interface TelecomOperatorList {
  operators: TelecomOperator[];
  count: number;
  registry: { version: string; updated: string; operators: string };
}

export function getTelecomOperators(
  country?: string,
  signal?: AbortSignal
): Promise<TelecomOperatorList> {
  const query = country ? `?country=${encodeURIComponent(country)}` : "";
  return requestJson<TelecomOperatorList>(
    `/api/v1/telecom/operators${query}`,
    signal
  );
}

export interface TelecomNumberParse {
  e164_masked: string;
  country: string | null;
  operator_id: string | null;
  basis: string;
  limitation: string;
}

export function parseTelecomNumber(
  e164: string,
  signal?: AbortSignal
): Promise<TelecomNumberParse> {
  return requestJson<TelecomNumberParse>(
    `/api/v1/telecom/numbers/parse?e164=${encodeURIComponent(e164)}`,
    signal
  );
}

export interface TelecomVerification {
  verification_id: string;
  subject_masked: string;
  subject_hash: string;
  operator_id: string | null;
  country: string | null;
  provider: string;
  provider_ref: string;
  api: string;
  api_version: string;
  verify_type: string;
  state: string;
  previous_state: string;
  confidence: string;
  source: string;
  verified_at: string;
  verified_ts: number;
  freshness_ttl_hours: number;
  limitations: string[];
  consent_id: string;
  purpose: string;
  org: string;
  user: string;
  tenant_id: string;
  synthetic: boolean;
  evidence: Record<string, string>;
  record_hash: string;
  integrity?: string;
}

export function requestTelecomVerification(
  body: {
    verify_type: string;
    e164: string;
    purpose: string;
    context?: Record<string, string>;
  },
  signal?: AbortSignal
): Promise<TelecomVerification> {
  return postJson<TelecomVerification>(
    "/api/v1/telecom/verifications",
    body,
    signal
  );
}

export function getTelecomVerification(
  verificationId: string,
  signal?: AbortSignal
): Promise<TelecomVerification> {
  return requestJson<TelecomVerification>(
    `/api/v1/telecom/verifications/${encodeURIComponent(verificationId)}`,
    signal
  );
}

export interface TelecomSummary {
  history: {
    verification_id: string;
    verify_type: string;
    state: string;
    verified_at: string;
    stale: boolean;
  }[];
  co_signals: {
    devices: string[];
    accounts: string[];
    beneficiaries: string[];
    geo_labels: string[];
    transaction_count: number;
  };
  history_count: number;
  subject_masked: string;
  allocation: {
    operator_id: string | null;
    country: string | null;
    basis: string;
    limitation: string;
  };
  phone_label: string;
}

export function getTelecomSummary(
  params: { subject?: string; phone_label?: string },
  signal?: AbortSignal
): Promise<TelecomSummary> {
  const query = new URLSearchParams();
  if (params.subject) query.set("subject", params.subject);
  if (params.phone_label) query.set("phone_label", params.phone_label);
  return requestJson<TelecomSummary>(
    `/api/v1/telecom/summary?${query.toString()}`,
    signal
  );
}

export interface TelecomConfig {
  registry: { version: string; updated: string; operators: string };
  tracked_apis: string[];
  verify_types: string[];
  consent_required_all: boolean;
  always_consent_types: string[];
  retention_days: number;
  actor_per_min: number;
  subject_per_day: number;
  providers: {
    adapter: string;
    name: string;
    status: string;
    live: boolean;
    secret_refs: string[];
    secret_present: Record<string, boolean>;
  }[];
  live_integrations: string[];
}

export function getTelecomConfig(
  signal?: AbortSignal
): Promise<TelecomConfig> {
  return requestJson<TelecomConfig>("/api/v1/admin/telecom-config", signal);
}

/* Geointelligence OS clients. Shapes mirror app/identity_verify.py,
 * app/address_verify.py, app/location_obs.py, app/ip_intel.py,
 * app/intel_providers.py, app/investigation_map.py,
 * app/intel_auth.py. Sensitive reads are masked for auditors and
 * denied for viewers (enforced server-side). */

export interface IdentityVerification {
  verification_id: string;
  tenant_id: string;
  investigation_id: string;
  subject_hash: string;
  subject_masked: string;
  provider_id: string;
  verify_type: string;
  verification_status: string;
  previous_status: string;
  country: string;
  factors: {
    factor: string;
    result: string;
    evidence_ref: string;
    reliability: string;
  }[];
  missing: string[];
  limitations: string[];
  evidence_reference: string;
  attributes_checked: string[];
  verified_at: string;
  verified_ts: number;
  expires_at: number;
  purpose: string;
  org: string;
  user: string;
  synthetic: boolean;
  record_hash: string;
  integrity?: string;
  masked_view?: boolean;
}

export function requestIdentityVerification(
  body: {
    verify_type: string;
    subject_ref: string;
    attributes?: Record<string, string>;
    country: string;
    purpose: string;
    investigation_id?: string;
  },
  signal?: AbortSignal
): Promise<IdentityVerification> {
  return postJson<IdentityVerification>(
    "/api/v1/identity/verifications",
    body,
    signal
  );
}

export function getIdentityVerification(
  verificationId: string,
  signal?: AbortSignal
): Promise<IdentityVerification> {
  return requestJson<IdentityVerification>(
    `/api/v1/identity/verifications/${encodeURIComponent(verificationId)}`,
    signal
  );
}

export interface AddressVerification {
  verification_id: string;
  tenant_id: string;
  investigation_id: string;
  subject_hash: string;
  subject_masked: string;
  address?: Record<string, string>;
  address_masked: {
    country: string;
    region: string;
    state_province: string;
    district: string;
    city: string;
    street_masked: string;
    has_coordinates: boolean;
  };
  provider_id: string;
  verification_method: string;
  verification_status: string;
  previous_status: string;
  match_result: Record<string, unknown>;
  limitations: string[];
  evidence_reference: string;
  verified_at: string;
  verified_ts: number;
  expires_at: number;
  purpose: string;
  org: string;
  user: string;
  synthetic: boolean;
  record_hash: string;
  integrity?: string;
  masked_view?: boolean;
}

export function requestAddressVerification(
  body: {
    address: Record<string, string>;
    subject_ref: string;
    method: string;
    purpose: string;
    investigation_id?: string;
    geocoded_only?: boolean;
  },
  signal?: AbortSignal
): Promise<AddressVerification> {
  return postJson<AddressVerification>(
    "/api/v1/addresses/verify",
    body,
    signal
  );
}

export function getAddressVerification(
  verificationId: string,
  signal?: AbortSignal
): Promise<AddressVerification> {
  return requestJson<AddressVerification>(
    `/api/v1/addresses/verifications/${encodeURIComponent(verificationId)}`,
    signal
  );
}

export interface IpLookupResult {
  status: string;
  location: {
    country_code: string | null;
    region: string | null;
    city: string | null;
    latitude: number | null;
    longitude: number | null;
    accuracy_km: number | null;
  };
  network: {
    asn: string | null;
    organization: string | null;
    vpn_indicator: string;
    proxy_indicator: string;
    tor_indicator: string;
  };
  source: {
    provider: string | null;
    observed_at: string | null;
    retrieved_at: string | null;
  };
  investigation_id: string;
  purpose: string;
  limitations: string[];
  observation_id: string;
}

export function postIpLookup(
  body: { ip_address: string; investigation_id?: string; purpose: string },
  signal?: AbortSignal
): Promise<IpLookupResult> {
  return postJson<IpLookupResult>(
    "/api/v1/geolocation/ip/lookup",
    body,
    signal
  );
}

export interface LocationObservation {
  observation_id: string;
  tenant_id: string;
  investigation_id: string;
  subject_hash: string;
  subject_masked: string;
  device_reference: string;
  source_type: string;
  provider_id: string;
  latitude?: number;
  longitude?: number;
  accuracy_meters: number | "unknown";
  observed_at: string;
  received_at: string;
  timezone: string;
  method: string;
  verification_status: string;
  authorization_reference: string;
  consent_reference: string;
  evidence_reference: string;
  expires_at: number;
  created_at: string;
  record_hash: string;
  integrity?: string;
  masked_view?: boolean;
}

export interface IntelMap {
  investigation_id: string;
  layers: Record<
    string,
    {
      items: Record<string, unknown>[];
      item_count: number;
      reason_if_empty: string;
    }
  >;
  masked: boolean;
  masked_view?: boolean;
  map_provider_note: string;
}

export function getInvestigationMap(
  investigationId: string,
  signal?: AbortSignal
): Promise<IntelMap> {
  return requestJson<IntelMap>(
    `/api/v1/investigations/${encodeURIComponent(investigationId)}/map`,
    signal
  );
}

export interface IntelRelationship {
  edge_id: string;
  source: string;
  target: string;
  relationship_type: string;
  strength: string;
  evidence_reference: string;
  provider: string;
  valid_from: string;
  valid_to: string;
}

export function getInvestigationRelationships(
  investigationId: string,
  signal?: AbortSignal
): Promise<{ investigation_id: string; relationships: IntelRelationship[] }> {
  return requestJson(
    `/api/v1/investigations/${encodeURIComponent(investigationId)}/relationships`,
    signal
  );
}

export interface IntelProvider {
  provider_id: string;
  name: string;
  category: string;
  auth: string;
  capabilities: string[];
  api_version: string;
  integration_status: string;
  live: boolean;
  countries: string;
  cost_classification: string;
  limitations: string[];
  secret_refs: string[];
}

export function getIntelProviders(
  signal?: AbortSignal
): Promise<{ providers: IntelProvider[]; count: number }> {
  return requestJson("/api/v1/providers", signal);
}

export interface CountryCoverage {
  country: string;
  country_name: string;
  identity: string;
  telecom: string;
  address: string;
  ip_geolocation: string;
  mapping: string;
  location: string;
  operators_registered: string[];
  overall: string;
  legal_review: string;
  note: string;
}

export function getIntelCoverage(
  signal?: AbortSignal
): Promise<{
  countries: CountryCoverage[];
  count: number;
  map_provider: string;
}> {
  return requestJson("/api/v1/geointel/coverage", signal);
}

export function getIntelMetrics(
  signal?: AbortSignal
): Promise<{
  tenant_id: string;
  counts: Record<string, { total: number; by_status: Record<string, number> }>;
  computed_live: boolean;
  history: string;
}> {
  return requestJson("/api/v1/geointel/metrics", signal);
}

/* UFI: universal financial crime intelligence. Shapes mirror
 * app/payment_methods.py, parties.py, typologies.py, alerts.py,
 * tracing.py, altpayments.py and reports.py exactly. */

export interface TraceMovement {
  from_transaction: string;
  to_transaction: string;
  hop: number;
  status: string;
  evidence: string;
  amount_minor: number | null;
  currency: string | null;
}

export interface FundTrace {
  trace_id: string;
  origin_transaction: string;
  movements: TraceMovement[];
  visited_transactions: string[];
  limitations: string[];
  built_at: string;
}

export function postTrace(
  transactionId: string,
  maxHops = 4,
  signal?: AbortSignal
): Promise<FundTrace> {
  return postJson<FundTrace>(
    "/api/v1/tracing/transactions",
    { transaction_id: transactionId, max_hops: maxHops },
    signal
  );
}

export function getTrace(
  traceId: string,
  signal?: AbortSignal
): Promise<FundTrace> {
  return requestJson<FundTrace>(
    `/api/v1/tracing/${encodeURIComponent(traceId)}`,
    signal
  );
}

export interface Typology {
  typology_id: string;
  label: string;
  detector_families: string[];
  engine_rules: string[];
  industries: string[];
  industry_taxonomy_codes: string[];
  detection_gap: boolean;
  mapping_errors: string[];
  matched_signal_ids?: string[];
  matched_count?: number;
}

export function getTypologies(
  industry?: string,
  signal?: AbortSignal
): Promise<{ typologies: Typology[] }> {
  const query = industry ? `?industry=${encodeURIComponent(industry)}` : "";
  return requestJson(`/api/v1/fraud/typologies${query}`, signal);
}

export function getTypology(
  typologyId: string,
  signal?: AbortSignal
): Promise<Typology> {
  return requestJson<Typology>(
    `/api/v1/fraud/typologies/${encodeURIComponent(typologyId)}`,
    signal
  );
}

export interface Party {
  role: string;
  reference_masked: string | null;
  label: string | null;
  source_field: string;
  verification: string;
}

export interface TxnParties {
  transaction_id: string;
  parties: Party[];
  classification: {
    method_id: string;
    confidence: string;
    explanation: string;
  };
  network: {
    institution_id: string;
    confidence: string;
    explanation: string;
  };
  tenant_scope: string;
}

export function getTxnParties(
  txnId: string,
  signal?: AbortSignal
): Promise<TxnParties> {
  return requestJson<TxnParties>(
    `/api/v1/transactions/${encodeURIComponent(txnId)}/parties`,
    signal
  );
}

async function patchJson<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal
): Promise<T> {
  /* PATCH twin of postJson for alert transitions. */
  const init: RequestInit = {
    method: "PATCH",
    signal,
    credentials: "include",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
  const gate = deadline(signal);
  init.signal = gate.signal;
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl()}${path}`, init);
  } catch (err: unknown) {
    throw toNetworkError(err);
  } finally {
    gate.clear();
  }
  const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
  if (!res.ok) {
    notifyUnauthorized(path, res.status);
    throw new ApiError(
      data.error ?? `request failed (${res.status})`,
      res.status,
      data
    );
  }
  return data as T;
}

export interface FraudAlert {
  id: string;
  signal_id: string;
  transaction_id: string | null;
  detector_family: string | null;
  severity: string | null;
  status: string;
  opened_at: string;
  history: { status: string; at: string; actor: string }[];
  notified: boolean;
}

export function getFraudAlerts(
  status?: string,
  signal?: AbortSignal
): Promise<{ alerts: FraudAlert[]; tenant_scope: string }> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return requestJson(`/api/v1/fraud/alerts${query}`, signal);
}

export function postFraudAlert(
  signalId: string,
  signal?: AbortSignal
): Promise<{ status: string; alert: FraudAlert }> {
  return postJson("/api/v1/fraud/alerts", { signal_id: signalId }, signal);
}

export function patchFraudAlert(
  alertId: string,
  status: string,
  signal?: AbortSignal
): Promise<FraudAlert> {
  return patchJson<FraudAlert>(
    `/api/v1/fraud/alerts/${encodeURIComponent(alertId)}`,
    { status },
    signal
  );
}

/* UFI slice 2: monitoring + industry adapters. Shapes mirror
 * app/monitoring.py and app/industry_adapters.py exactly. */

export interface MonitoringStatus {
  mode: string;
  mode_note: string;
  tenant_scope: string;
  transactions_visible: number;
  signals_visible: number;
  alerts_open: number;
  alerts_by_status: Record<string, number>;
  signals_without_alerts: number;
  data_window: { start: string | null; end: string | null };
  computed_at: string;
}

export function getMonitoringStatus(
  signal?: AbortSignal
): Promise<MonitoringStatus> {
  return requestJson<MonitoringStatus>("/api/v1/monitoring/status", signal);
}

export interface MonitoringRun {
  tenant_scope: string;
  signals_evaluated: number;
  alerts_opened: string[];
  alerts_duplicate: string[];
  family_runs: Record<string, number>;
  family_errors: { family: string; error: string }[];
  evaluated_at: string;
}

export function postMonitoringEvaluate(
  signal?: AbortSignal
): Promise<MonitoringRun> {
  return postJson<MonitoringRun>("/api/v1/monitoring/evaluate", {}, signal);
}

export interface IndustryEntry {
  id: string;
  name: string;
  status: string;
  shared_reuse?: string[];
  note?: string;
  status_evidence?: string;
}

export function getIndustries(
  signal?: AbortSignal
): Promise<{ industries: IndustryEntry[]; count: number }> {
  return requestJson("/api/v1/industries", signal);
}

export interface IndustryCoverage {
  industry_id: string;
  name: string;
  registry_status: string;
  risk_taxonomy_codes: (string | undefined)[];
  threat_scenarios: number;
  typologies: string[];
  test_file: string | null;
  test_present: boolean;
}

export function getIndustryCoverage(
  industryId: string,
  signal?: AbortSignal
): Promise<IndustryCoverage> {
  return requestJson<IndustryCoverage>(
    `/api/v1/industries/${encodeURIComponent(industryId)}/coverage`,
    signal
  );
}

export interface IndustryReadiness {
  industry_id: string;
  registry_status: string;
  checks: {
    profile_present: boolean;
    tests_present: boolean;
    typologies_mapped: boolean;
    typologies_measured: boolean;
    status_gate: boolean;
  };
  typologies_measured: number;
  overall: string;
  note: string;
}

export function getIndustryReadiness(
  industryId: string,
  signal?: AbortSignal
): Promise<IndustryReadiness> {
  return requestJson<IndustryReadiness>(
    `/api/v1/industries/${encodeURIComponent(industryId)}/readiness`,
    signal
  );
}

/* Agent OS: conversations + orchestrated runs. Shapes mirror
 * app/conversations.py, app/orchestration.py and app/nl_search.py. */

export interface ConversationMessage {
  role: string;
  text: string;
  at: string;
}

export interface Conversation {
  conversation_id: string;
  tenant_id: string;
  owner: string;
  context: Record<string, string>;
  messages: ConversationMessage[];
  created_at: string;
  expires_at: string;
}

export function postConversation(
  context: Record<string, string>,
  signal?: AbortSignal
): Promise<Conversation> {
  return postJson<Conversation>(
    "/api/v1/conversations",
    { context },
    signal
  );
}

export function getConversation(
  conversationId: string,
  signal?: AbortSignal
): Promise<Conversation> {
  return requestJson<Conversation>(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}`,
    signal
  );
}

export interface OrchestratedTurn {
  user_message: ConversationMessage;
  assistant_message: ConversationMessage;
  execution: {
    execution_id: string;
    state: string;
    classification?: { intent: string; rationale: string };
    steps: {
      tool: string;
      status: string;
      plan_id?: string;
      error?: string;
    }[];
    error: string;
  };
}

export function postConversationMessage(
  conversationId: string,
  text: string,
  signal?: AbortSignal
): Promise<OrchestratedTurn> {
  return postJson<OrchestratedTurn>(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
    { text },
    signal
  );
}

export interface NlSearchResult {
  query: {
    filters: Record<string, string | number | boolean>;
    notes: string[];
    needs_clarification?: boolean;
    question?: string;
  };
  results: {
    count: number;
    capped: boolean;
    transactions: {
      transaction_id: string;
      channel: string;
      amount_minor: number;
      currency: string;
      occurred_at: string;
      flagged: boolean;
    }[];
    explanation: string;
  } | null;
}

export function postNlSearch(
  text: string,
  signal?: AbortSignal
): Promise<NlSearchResult> {
  return postJson<NlSearchResult>(
    "/api/v1/agent-os/search",
    { text },
    signal
  );
}

/* Recovery OS: eligibility, cases, capability matrix, metrics.
 * Shapes mirror app/recovery.py, recovery_rules.py and
 * recovery_caps.py exactly. */

export interface EligibilityResult {
  status: string;
  rule_id: string | null;
  reason: string;
  missing: string[];
  alternatives: string[];
}

export function postRecoveryAssess(
  transactionId: string,
  reason: string,
  signal?: AbortSignal
): Promise<EligibilityResult> {
  return postJson<EligibilityResult>(
    "/api/v1/recovery/assess",
    { transaction_id: transactionId, reason },
    signal
  );
}

export interface RecoveryCase {
  recovery_id: string;
  transaction_id: string;
  reason: string;
  state: string;
  eligibility: EligibilityResult | null;
  evidence: { kind: string; reference: string }[];
  channel: string | null;
  external_reference: string | null;
  history: { state: string; at: string; actor: string; note: string }[];
}

export function getRecoveryCases(
  signal?: AbortSignal
): Promise<{ cases: RecoveryCase[]; tenant_scope: string }> {
  return requestJson("/api/v1/recovery/cases", signal);
}

export function postRecoveryCase(
  transactionId: string,
  reason: string,
  signal?: AbortSignal
): Promise<{ status: string; case: RecoveryCase }> {
  return postJson(
    "/api/v1/recovery/cases",
    { transaction_id: transactionId, reason },
    signal
  );
}

export interface RecoveryMetrics {
  total: number;
  by_state: Record<string, number>;
  by_reason: Record<string, number>;
  tenant_scope: string;
  window: string;
}

export function getRecoveryMetrics(
  signal?: AbortSignal
): Promise<RecoveryMetrics> {
  return requestJson<RecoveryMetrics>(
    "/api/v1/recovery/metrics",
    signal
  );
}

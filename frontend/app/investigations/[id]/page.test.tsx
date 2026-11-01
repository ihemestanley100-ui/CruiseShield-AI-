import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import type {
  AgentRun,
  EvidencePackage,
  InvestigationDetail,
} from "../../../lib/api";
import InvestigationPage from "./page";

const {
  getInvestigationMock,
  getEvidencePackageMock,
  postAiAnalysisMock,
  getInvestigationIntelMock,
  getIntelEvidenceMock,
  getRiskIntelMock,
} = vi.hoisted(() => ({
  getInvestigationMock: vi.fn(),
  getEvidencePackageMock: vi.fn(),
  postAiAnalysisMock: vi.fn(),
  getInvestigationIntelMock: vi.fn(),
  getIntelEvidenceMock: vi.fn(),
  getRiskIntelMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "inv_84721" }),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getInvestigation: getInvestigationMock,
  getEvidencePackage: getEvidencePackageMock,
  postAiAnalysis: postAiAnalysisMock,
  getInvestigationIntel: getInvestigationIntelMock,
  getIntelEvidence: getIntelEvidenceMock,
  getRiskIntel: getRiskIntelMock,
}));

function detailFixture(): InvestigationDetail {
  return {
    investigation: {
      investigation_id: "inv_84721",
      alert_id: "alert_84721",
      transaction_id: "txn_84721",
      status: "OPEN",
    },
    alert: { alert_id: "alert_84721", title: "HIGH network risk", status: "OPEN" },
    transaction: {
      transaction_id: "txn_84721",
      amount_minor: 48000000,
      currency: "NGN",
      channel: "MOBILE_APP",
      sender_account_id: "acct_A",
      receiver_account_id: "acct_B",
      occurred_at: "2026-10-27T10:00:00Z",
    },
    risk_transaction: {
      risk_assessment_id: "risk_transaction_84721",
      target_id: "txn_84721",
      target_type: "transaction",
      score: 35,
      band: "MODERATE",
      score_version: "risk-score-v1",
      computed_at: "2026-10-28T00:00:00Z",
      limitations: "Demo score.",
    },
    risk_network: {
      risk_assessment_id: "risk_network_84721",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "2026-10-28T00:00:00Z",
      limitations: "Demo score.",
    },
    rule_results: [
      {
        rule_result_id: "rr_R-001_84721",
        rule_id: "R-001",
        rule_version: "1.0",
        triggered: true,
        threshold: "amount_minor >= 40000000",
        explanation: "Observed 48000000 kobo.",
        source_record_ids: ["txn_84721"],
        evidence_ids: ["evidence_rr_R-001_84721"],
        trace_id: "t",
      },
    ],
    case: { case_id: "case_84721", status: "TRIAGED" },
    evidence_package_id: "evidence_pkg_scn_primary_1.0.0",
    evidence_count: 1,
  };
}

function packageFixture(): EvidencePackage {
  return {
    package_id: "evidence_pkg_scn_primary_1.0.0",
    scenario_id: "scn_primary",
    package_hash: "abc",
    items: [
      {
        evidence_id: "evidence_txn_84721",
        evidence_type: "transaction",
        title: "Transaction #84721",
        description: "Synthetic demo record.",
        event_ids: ["evt_demo_84721"],
        graph_edge_ids: [],
        rule_result_ids: [],
      },
    ],
  };
}

beforeEach(() => {
  getInvestigationMock.mockReset();
  getEvidencePackageMock.mockReset();
  postAiAnalysisMock.mockReset();
  getInvestigationIntelMock.mockReset();
  getIntelEvidenceMock.mockReset();
  getRiskIntelMock.mockReset();
  getInvestigationIntelMock.mockRejectedValue(new Error("intel down"));
  getIntelEvidenceMock.mockRejectedValue(new Error("intel down"));
  getRiskIntelMock.mockRejectedValue(new Error("intel down"));
  // Deterministic badge values: reduced motion renders the authoritative
  // final score immediately instead of converging to it on the wall clock
  // via rAF. Animation timing itself is covered by use-count-up.test.tsx
  // and risk-badge.test.tsx with fake timers; these page tests assert the
  // same final text, so no assertion is weakened.
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("InvestigationPage", () => {
  it("renders loading then live data", async () => {
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    render(<InvestigationPage />);
    expect(screen.getByText("Loading investigation…")).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByText(/₦480,000/)).toBeTruthy();
    });
    // Reduced motion (stubbed above) renders the authoritative final score
    // immediately; this wait covers the async data load only.
    await waitFor(() => {
      expect(screen.getByText(/84\/100 HIGH/)).toBeTruthy();
    });
    expect(
      screen.getByText(
        (content, element) =>
          element?.tagName === "STRONG" &&
          content.startsWith("R-001") &&
          content.includes("triggered")
      )
    ).toBeTruthy();
    expect(screen.getByText("evidence_rr_R-001_84721")).toBeTruthy();
    expect(screen.getByText("evidence_txn_84721")).toBeTruthy();
  });

  it("maps the badge to the API network score, never a hardcoded value", async () => {
    const detail = detailFixture();
    detail.risk_network = { ...detail.risk_network, score: 72, band: "HIGH" };
    getInvestigationMock.mockResolvedValue(detail);
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    render(<InvestigationPage />);
    await waitFor(() => {
      expect(screen.getByText(/72\/100 HIGH/)).toBeTruthy();
    });
    expect(screen.queryByText(/84\/100/)).toBeNull();
    expect(
      screen.getByLabelText("Risk 72 of 100, HIGH")
    ).toBeTruthy();
  });

  it("renders section navigation matching real section anchors", async () => {
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    const { container } = render(<InvestigationPage />);
    const nav = await screen.findByRole("navigation", { name: "On this page" });
    const hrefs = [...nav.querySelectorAll("a")].map((a) =>
      a.getAttribute("href")
    );
    expect(hrefs).toEqual([
      "#overview-h",
      "#why-risk-h",
      "#evidence-h",
      "#intel-h",
      "#ai-h",
    ]);
    for (const href of hrefs) {
      expect(container.querySelector(href as string)).not.toBeNull();
    }
  });

  it("shows an error card when the backend fails", async () => {
    getInvestigationMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    render(<InvestigationPage />);
    await waitFor(() => {
      expect(screen.getByText(/BACKEND_UNREACHABLE/)).toBeTruthy();
    });
  });

  it("shows a not-found panel for unknown ids", async () => {
    getInvestigationMock.mockRejectedValue(
      new ApiError("UNKNOWN_INVESTIGATION", "nope", 404, "")
    );
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    render(<InvestigationPage />);
    await waitFor(() => {
      expect(screen.getByText("Investigation not found")).toBeTruthy();
    });
  });

  it("keeps deterministic evidence intact when analysis fails", async () => {
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    postAiAnalysisMock.mockRejectedValue(
      new ApiError("MODEL_TIMEOUT", "timed out", 503, "")
    );
    render(<InvestigationPage />);
    await waitFor(() => {
      expect(screen.getByText(/₦480,000/)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText(/MODEL_TIMEOUT/)).toBeTruthy();
    });
    // Reduced motion (stubbed above) renders the authoritative final score
    // immediately; this wait covers the async data load only.
    await waitFor(() => {
      expect(screen.getByText(/84\/100 HIGH/)).toBeTruthy();
    });
    expect(screen.getByText("evidence_txn_84721")).toBeTruthy();
  });

  it("keeps risk and evidence intact when analysis succeeds", async () => {
    const run: AgentRun = {
      agent_run_id: "agentrun_9",
      model_id: "muse-spark-1.3",
      prompt_version: "cs-prompt-v2",
      request_id: "req_9",
      latency_ms: 1200,
      status: "SUCCEEDED",
      schema_validation_status: "VALIDATED",
      evidence_reference_validation_status: "VALIDATED",
      error_code: "",
      result: {
        summary: "Seeded network shows shared infrastructure.",
        key_findings: [],
        alternative_explanations: [],
        missing_information: [],
        conclusion: "requires_review",
        disclaimer: "Advisory only.",
      },
    };
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    postAiAnalysisMock.mockResolvedValue(run);
    render(<InvestigationPage />);
    await waitFor(() => {
      expect(screen.getByText(/₦480,000/)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText(/shared infrastructure/)).toBeTruthy();
    });
    // Reduced motion (stubbed above) renders the authoritative final score
    // immediately; this wait covers the async data load only.
    await waitFor(() => {
      expect(screen.getByText(/84\/100 HIGH/)).toBeTruthy();
    });
    expect(screen.getByText("evidence_txn_84721")).toBeTruthy();
  });

  it("shows breadcrumbs with route params on every state", async () => {
    getInvestigationMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    getEvidencePackageMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    render(<InvestigationPage />);
    const nav = await screen.findByRole("navigation", { name: "Breadcrumb" });
    expect(nav.querySelector("a")?.getAttribute("href")).toBe("/demo");
    expect(
      within(nav).getByText("Investigation inv_84721").getAttribute("aria-current")
    ).toBe("page");
  });

  it("renders the intel section when DI fetches succeed (DI-10)", async () => {
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    getInvestigationIntelMock.mockResolvedValue({
      investigation_id: "inv_84721",
      transaction_id: "txn_84721",
      transaction_intel: {
        transaction_id: "txn_84721",
        device_observations: [],
        ip_observations: [],
        geolocation_observations: [],
      },
      isolation: "own-transaction only",
      synthetic: true,
      limitations: [],
    });
    getIntelEvidenceMock.mockResolvedValue({
      investigation_id: "inv_84721",
      findings: [],
      trace: null,
      synthetic: true,
    });
    getRiskIntelMock.mockResolvedValue({
      engine: "risk-intelligence-v2-candidate",
      enabled: false,
    });
    render(<InvestigationPage />);
    await waitFor(() =>
      expect(screen.getByTestId("intel-status")).toHaveTextContent(
        "0 finding(s)"
      )
    );
    expect(
      screen.getByText(/candidate engine.*is OFF \(default\)/i)
    ).toBeTruthy();
  });

  it("renders the page when DI fetches fail (DI-10)", async () => {
    getInvestigationMock.mockResolvedValue(detailFixture());
    getEvidencePackageMock.mockResolvedValue(packageFixture());
    render(<InvestigationPage />);
    await waitFor(() =>
      expect(screen.getByTestId("intel-status")).toHaveTextContent(
        "Intelligence unavailable for this investigation."
      )
    );
    expect(screen.getByText("evidence_txn_84721")).toBeTruthy();
  });
});

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import type {
  GraphResponse,
  OverlayResponse,
  TransactionResponse,
  TxnIntel,
  TxnSignals,
} from "../../../lib/api";
import NetworkPage from "./page";

const {
  getGraphMock,
  getOverlayMock,
  getTransactionMock,
  getTransactionIntelMock,
  getTxnSignalsMock,
} = vi.hoisted(() => ({
  getGraphMock: vi.fn(),
  getOverlayMock: vi.fn(),
  getTransactionMock: vi.fn(),
  getTransactionIntelMock: vi.fn(),
  getTxnSignalsMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ txnId: "txn_84721" }),
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
  getGraph: getGraphMock,
  getGraphOverlay: getOverlayMock,
  getTransaction: getTransactionMock,
  getTransactionIntel: getTransactionIntelMock,
  getTxnSignals: getTxnSignalsMock,
}));

function graphFixture(): GraphResponse {
  return {
    transaction_id: "txn_84721",
    nodes: [
      {
        node_id: "acct_A",
        node_type: "account",
        display_label: "Account A",
        synthetic_flag: true,
        source_record_ids: ["seed:scn_primary:acct_A"],
      },
      {
        node_id: "acct_B",
        node_type: "account",
        display_label: "Account B",
        synthetic_flag: true,
        source_record_ids: ["seed:scn_primary:acct_B"],
      },
    ],
    edges: [
      {
        edge_id: "edge_0001",
        source_node_id: "acct_A",
        target_node_id: "acct_B",
        relationship_type: "SENT_TO",
        source_event_ids: ["evt_84721"],
        evidence_ids: ["evidence_edge_0001"],
        valid_from: "2026-10-27T10:00:00Z",
        valid_to: null,
        synthetic_flag: true,
        trace_id: "trace_84721",
      },
    ],
    provenance_errors: [],
    counts: { nodes: 2, edges: 1 },
  };
}

function overlayFixture(): OverlayResponse {
  return {
    transaction_id: "txn_84721",
    nodes: [
      {
        node_id: "ip_8.8.8.8",
        node_type: "ip",
        display_label: "IP 8.8.8.8",
        synthetic_flag: true,
        source_record_ids: ["obs_ip_1"],
      },
    ],
    edges: [],
    node_details: {},
    unavailable: { location: "labels_without_geo:loc_01" },
    counts: {
      overlay_nodes: 1,
      overlay_edges: 0,
      base_nodes: 2,
      base_edges: 1,
    },
    derived: true,
    synthetic: true,
  };
}

function emptyOverlay(): OverlayResponse {
  return {
    ...overlayFixture(),
    nodes: [],
    edges: [],
    unavailable: {},
    counts: {
      overlay_nodes: 0,
      overlay_edges: 0,
      base_nodes: 2,
      base_edges: 1,
    },
  };
}

function txnFixture(): TransactionResponse {
  return {
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
      limitations: "Risk score.",
    },
    risk_network: {
      risk_assessment_id: "risk_network_84721",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "2026-10-28T00:00:00Z",
      limitations: "Risk score.",
    },
  };
}

function txnIntelFixture(): TxnIntel {
  return {
    transaction_id: "txn_84721",
    source_account_id: "acct_A",
    destination_account_id: "acct_B",
    transaction_time: "2026-10-27T10:00:00Z",
    device_observations: [
      {
        obs_id: "o1",
        device_id: "dev_04",
        account_id: "acct_A",
        txn_id: "txn_84721",
        observed_at: "2026-10-27T10:00:00Z",
        source: "seed_event",
        source_ref: "evt_1",
        synthetic: true,
      },
      {
        obs_id: "o2",
        device_id: "dev_04",
        account_id: "acct_B",
        txn_id: "txn_84721",
        observed_at: "2026-10-27T11:00:00Z",
        source: "seed_event",
        source_ref: "evt_2",
        synthetic: true,
      },
    ],
    ip_observations: [],
    geolocation_observations: [],
    device_graph_refs: { dev_04: ["edge_1"] },
    observation_first_seen: "2026-10-27T10:00:00Z",
    observation_last_seen: "2026-10-27T11:00:00Z",
    provenance: { event_ids: ["evt_1"] },
    synthetic: true,
    limitations: ["fixture-derived"],
  };
}

beforeEach(() => {
  getGraphMock.mockReset();
  getOverlayMock.mockReset();
  getTransactionMock.mockReset();
  getTransactionIntelMock.mockReset();
  getTxnSignalsMock.mockReset();
  getOverlayMock.mockResolvedValue(emptyOverlay());
  getTransactionMock.mockResolvedValue(txnFixture());
  // DI-06 intel is best-effort: default to unavailable so existing tests
  // assert the page without it; intel tests override per case.
  getTransactionIntelMock.mockRejectedValue(new Error("intel down"));
  // Detection drill-down is best-effort too: hidden unless provided.
  getTxnSignalsMock.mockRejectedValue(new Error("signals down"));
  // Same reduced-motion stub as the investigation page tests: the
  // header badge renders its authoritative final value immediately.
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

describe("NetworkPage", () => {
  it("renders the exact backend counts, graph and table", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    const { container } = render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("network-counts")).toHaveTextContent(
        "2 nodes, 1 edges"
      )
    );
    expect(getGraphMock).toHaveBeenCalledWith("txn_84721", expect.anything());
    expect(container.querySelectorAll("[data-node]")).toHaveLength(2);
    expect(container.querySelectorAll("[data-edge]")).toHaveLength(1);
    expect(container.querySelectorAll("[data-edge-row]")).toHaveLength(1);
  });

  it("defaults to the orbital view with a working flat fallback", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
        "2 of 2 nodes"
      )
    );
    fireEvent.click(screen.getByLabelText("Flat (fallback)"));
    expect(screen.getByTestId("graph-counts")).toHaveTextContent(
      "Showing 2 of 2 nodes, 1 of 1 edges."
    );
    expect(screen.queryByTestId("orbital-counts")).toBeNull();
    fireEvent.click(screen.getByLabelText("Orbital"));
    expect(screen.getByTestId("orbital-counts")).toBeTruthy();
  });

  it("shows a not-found state for an unknown transaction", async () => {
    getGraphMock.mockRejectedValue(
      new ApiError("UNKNOWN_TRANSACTION", "unknown txn", 404, "t")
    );
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByText("Transaction not found")).toBeTruthy()
    );
    expect(screen.getByText("txn_84721")).toBeTruthy();
  });

  it("shows an error with retry when the backend is unreachable", async () => {
    getGraphMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<NetworkPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Backend unreachable. Check the platform server and retry.")
      ).toBeTruthy()
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("warns when the backend reports provenance errors", async () => {
    const fixture = graphFixture();
    fixture.provenance_errors = ["edge_0001"];
    getGraphMock.mockResolvedValue(fixture);
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByText(/Provenance errors:/)).toBeTruthy()
    );
    const alerts = screen.getAllByRole("alert");
    expect(
      alerts.some((a) => a.textContent?.includes("edge_0001"))
    ).toBe(true);
  });

  it("shows an empty state when the graph has no nodes", async () => {
    getGraphMock.mockResolvedValue({
      ...graphFixture(),
      nodes: [],
      edges: [],
      counts: { nodes: 0, edges: 0 },
    });
    render(<NetworkPage />);
    await waitFor(() =>
      expect(
        screen.getByText(
          "This transaction has no network graph in the backend."
        )
      ).toBeTruthy()
    );
  });

  it("shows breadcrumbs with route params on every state", async () => {
    getGraphMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    render(<NetworkPage />);
    const nav = await screen.findByRole("navigation", { name: "Breadcrumb" });
    expect(nav.querySelector("a")?.getAttribute("href")).toBe("/platform");
    expect(
      within(nav).getByText("Network txn_84721").getAttribute("aria-current")
    ).toBe("page");
  });

  it("merges overlay nodes and reports unavailable categories (DI-07)", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    getOverlayMock.mockResolvedValue(overlayFixture());
    const { container } = render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("overlay-status")).toHaveTextContent(
        "1 nodes, 0 edges"
      )
    );
    expect(screen.getByTestId("overlay-status")).toHaveTextContent(
      "location (labels_without_geo:loc_01)"
    );
    expect(screen.getByTestId("network-counts")).toHaveTextContent(
      "2 nodes, 1 edges"
    );
    expect(container.querySelectorAll("[data-node]")).toHaveLength(3);
  });

  it("renders the base graph when the overlay fails (DI-07)", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    getOverlayMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    const { container } = render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("overlay-status")).toHaveTextContent(
        "Intelligence overlay unavailable."
      )
    );
    expect(container.querySelectorAll("[data-node]")).toHaveLength(2);
  });

  it("renders the transaction header from the base record (GAP-012)", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByText(/Transaction #84721/)).toBeTruthy()
    );
    expect(screen.getByText(/₦480,000/)).toBeTruthy();
    expect(screen.getByText(/acct_A → acct_B/)).toBeTruthy();
    expect(
      screen.getByText(/transaction-only 35\/100 MODERATE/)
    ).toBeTruthy();
    expect(screen.getByText(/84\/100 HIGH/)).toBeTruthy();
    expect(getTransactionMock).toHaveBeenCalledWith(
      "txn_84721",
      expect.any(AbortSignal)
    );
  });

  it("renders device intel when the best-effort fetch succeeds (GAP-013)", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    getTransactionIntelMock.mockResolvedValue(txnIntelFixture());
    render(<NetworkPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Device, IP & location intelligence")
      ).toBeTruthy()
    );
    expect(screen.getByText(/dev_04/)).toBeTruthy();
    expect(screen.getByText(/shared device/)).toBeTruthy();
    expect(screen.getByText(/2 accounts/)).toBeTruthy();
  });

  it("hides the intel section when the best-effort fetch fails", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("network-counts")).toHaveTextContent(
        "2 nodes, 1 edges"
      )
    );
    expect(
      screen.queryByText("Device, IP & location intelligence")
    ).toBeNull();
  });

  it("renders transaction signals with an investigation link", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    const fixture: TxnSignals = {
      transaction_id: "txn_84721",
      signals: [
        {
          signal_id: "sig001",
          detector_family: "VELOCITY",
          detector_version: "1.0",
          rule_id: "R-002",
          rule_version: "1.0",
          transaction_id: "txn_84721",
          channel: "POS",
          severity: "medium",
          occurred_at: "2026-10-27T10:00:00Z",
          tenant_id: "org_primary",
          entities: { sender: "acct_A", receiver: "acct_B" },
          reason: "R-002 fired",
          evidence: {},
          outcome: "PENDING",
        },
      ],
      signal_count: 1,
      investigation: {
        investigation_id: "inv_84721",
        alert_id: "alert_84721",
        transaction_id: "txn_84721",
        status: "OPEN",
      },
      case: { case_id: "case_84721", status: "NEW" },
      audits: [],
      tenant_scope: "org_primary",
    };
    getTxnSignalsMock.mockResolvedValue(fixture);
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByText("Transaction signals")).toBeTruthy()
    );
    expect(screen.getByText("VELOCITY")).toBeTruthy();
    const link = screen.getByRole("link", { name: /Open investigation/ });
    expect(link.getAttribute("href")).toBe("/investigations/inv_84721");
  });

  it("hides the signals section when the best-effort fetch fails", async () => {
    getGraphMock.mockResolvedValue(graphFixture());
    render(<NetworkPage />);
    await waitFor(() =>
      expect(screen.getByTestId("network-counts")).toHaveTextContent(
        "2 nodes, 1 edges"
      )
    );
    expect(screen.queryByText("Transaction signals")).toBeNull();
  });
});

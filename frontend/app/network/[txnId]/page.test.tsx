import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import type { GraphResponse, OverlayResponse } from "../../../lib/api";
import NetworkPage from "./page";

const { getGraphMock, getOverlayMock } = vi.hoisted(() => ({
  getGraphMock: vi.fn(),
  getOverlayMock: vi.fn(),
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
        source_event_ids: ["evt_demo_84721"],
        evidence_ids: ["evidence_edge_0001"],
        valid_from: "2026-10-27T10:00:00Z",
        valid_to: null,
        synthetic_flag: true,
        trace_id: "trace_demo_84721",
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

beforeEach(() => {
  getGraphMock.mockReset();
  getOverlayMock.mockReset();
  getOverlayMock.mockResolvedValue(emptyOverlay());
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
        screen.getByText("BACKEND_UNREACHABLE: Failed to fetch")
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
    expect(nav.querySelector("a")?.getAttribute("href")).toBe("/demo");
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
});

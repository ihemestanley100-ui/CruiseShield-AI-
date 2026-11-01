import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import type { SimulationResult } from "../lib/api";
import { SimulationPanel } from "./simulation-panel";

const { getGraphMock, getRiskMock, postSimulationMock } = vi.hoisted(() => ({
  getGraphMock: vi.fn(),
  getRiskMock: vi.fn(),
  postSimulationMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getGraph: getGraphMock,
  getRisk: getRiskMock,
  postSimulation: postSimulationMock,
}));

function graphFixture() {
  const edge = (id: string, rel: string) => ({
    edge_id: id,
    source_node_id: "acct_A",
    target_node_id: "acct_B",
    relationship_type: rel,
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: [`evidence_${id}`],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  });
  return {
    transaction_id: "txn_84721",
    nodes: [],
    edges: [edge("edge_0001", "SENT_TO"), edge("edge_0002", "USES_DEVICE")],
    provenance_errors: [],
    counts: { nodes: 2, edges: 2 },
  };
}

function riskFixture() {
  return {
    assessment: {
      risk_assessment_id: "risk_network_84721",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "2026-10-28T00:00:00Z",
      limitations: "Demo score.",
    },
    rule_results: [],
  };
}

function simFixture(): SimulationResult {
  return {
    simulation_id: "sim_0001",
    scenario_id: "scn_primary",
    target_transaction_id: "txn_84721",
    ignored_edge_ids: ["edge_0002"],
    assumption: "Devices coincidental.",
    baseline_score: 84,
    simulated_score: 72,
    baseline_band: "HIGH",
    simulated_band: "HIGH",
    limitations: "Hypothetical recomputation on a filtered edge set.",
    created_at: "2026-10-29T00:00:00Z",
    trace_id: "t",
  };
}

beforeEach(() => {
  getGraphMock.mockReset();
  getRiskMock.mockReset();
  postSimulationMock.mockReset();
  getGraphMock.mockResolvedValue(graphFixture());
  getRiskMock.mockResolvedValue(riskFixture());
});

describe("SimulationPanel", () => {
  it("loads real edges and the authoritative baseline", async () => {
    render(<SimulationPanel defaultTxnId="txn_84721" />);
    await waitFor(() =>
      expect(screen.getByTestId("sim-baseline")).toHaveTextContent(
        "Authoritative baseline (network): 84/100 HIGH"
      )
    );
    // signal is optional in the api.ts contract; the panel passes none.
    expect(getGraphMock).toHaveBeenCalledWith("txn_84721");
    expect(getRiskMock).toHaveBeenCalledWith("txn_84721", "network");
    expect(screen.getByTestId("sim-edges")).toHaveTextContent("edge_0002");
  });

  it("runs with selected edges and labels the result simulated", async () => {
    postSimulationMock.mockResolvedValue(simFixture());
    render(<SimulationPanel defaultTxnId="txn_84721" />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Run simulation" })
      ).toHaveProperty("disabled", false)
    );
    fireEvent.click(screen.getByLabelText(/edge_0002/));
    fireEvent.change(screen.getByLabelText(/Assumption/), {
      target: { value: "Devices coincidental." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Run simulation" }));
    await waitFor(() =>
      expect(screen.getByTestId("sim-result")).toHaveTextContent("sim_0001")
    );
    expect(postSimulationMock).toHaveBeenCalledWith(
      "txn_84721",
      ["edge_0002"],
      "Devices coincidental."
    );
    const result = screen.getByTestId("sim-result");
    expect(result).toHaveTextContent("SIMULATED");
    expect(result).toHaveTextContent("baseline 84/100 HIGH");
    expect(result).toHaveTextContent("simulated 72/100 HIGH");
    expect(screen.getByTestId("sim-baseline")).toHaveTextContent(
      "Authoritative baseline (network): 84/100 HIGH"
    );
  });

  it("shows server errors without inventing a result", async () => {
    postSimulationMock.mockRejectedValue(
      new ApiError("UNKNOWN_EDGE", "unknown edge", 400, "t")
    );
    render(<SimulationPanel defaultTxnId="txn_84721" />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Run simulation" })
      ).toHaveProperty("disabled", false)
    );
    fireEvent.click(screen.getByRole("button", { name: "Run simulation" }));
    await waitFor(() =>
      expect(screen.getByText("UNKNOWN_EDGE: unknown edge")).toBeTruthy()
    );
    expect(screen.queryByTestId("sim-result")).toBeNull();
  });

  it("reports an unknown target transaction honestly", async () => {
    getGraphMock.mockRejectedValue(
      new ApiError("UNKNOWN_TRANSACTION", "no txn", 404, "t")
    );
    render(<SimulationPanel defaultTxnId="txn_nope" />);
    await waitFor(() =>
      expect(screen.getByTestId("sim-baseline")).toHaveTextContent(
        "Target unavailable: UNKNOWN_TRANSACTION: no txn"
      )
    );
    expect(
      screen.getByRole("button", { name: "Run simulation" })
    ).toHaveProperty("disabled", true);
  });
});

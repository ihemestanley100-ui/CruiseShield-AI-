import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import ReplayPage from "./page";

const { listScenariosMock, getReplayMock, getGraphMock, getRiskMock, resetDemoMock } =
  vi.hoisted(() => ({
    listScenariosMock: vi.fn(),
    getReplayMock: vi.fn(),
    getGraphMock: vi.fn(),
    getRiskMock: vi.fn(),
    resetDemoMock: vi.fn(),
  }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ scenarioId: "scn_primary" }),
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
  listScenarios: listScenariosMock,
  getReplay: getReplayMock,
  getGraph: getGraphMock,
  getRisk: getRiskMock,
  resetDemo: resetDemoMock,
}));

function replayFixture(cursor: number) {
  return {
    scenario_id: "scn_primary",
    cursor,
    total: 11,
    current_event:
      cursor === 0
        ? null
        : {
            event_id: "evt_demo_84721",
            event_type: "financial.transaction.created",
            occurred_at: "2026-10-27T10:00:00Z",
            source: "synthetic_demo",
            trace_id: "trace_demo_84721",
            transaction: {
              transaction_id: "txn_84721",
              amount_minor: 48000000,
              currency: "NGN",
              channel: "MOBILE_APP",
              sender_account_id: "acct_A",
              receiver_account_id: "acct_B",
              occurred_at: "2026-10-27T10:00:00Z",
            },
            entities: {},
          },
    cumulative_event_ids: [],
    cumulative_transaction_ids: [],
    cumulative_edge_ids: [],
    counts: { events: cursor, transactions: 1, edges: 0 },
  };
}

beforeEach(() => {
  listScenariosMock.mockReset();
  getReplayMock.mockReset();
  getGraphMock.mockReset();
  getRiskMock.mockReset();
  resetDemoMock.mockReset();
  listScenariosMock.mockResolvedValue({
    scenarios: [
      { scenario_id: "scn_primary", title: "Seeded suspicious network" },
    ],
    active_scenario_id: "scn_primary",
  });
  getReplayMock.mockImplementation(async (_id: string, cursor: number) =>
    replayFixture(cursor)
  );
  getGraphMock.mockResolvedValue({
    transaction_id: "txn_84721",
    nodes: [],
    edges: [],
    provenance_errors: [],
    counts: { nodes: 0, edges: 0 },
  });
  getRiskMock.mockResolvedValue({
    assessment: {
      risk_assessment_id: "r",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "t",
      limitations: "Demo.",
    },
    rule_results: [],
  });
});

describe("ReplayPage", () => {
  it("renders scenario title, replay and simulation sections", async () => {
    render(<ReplayPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Replay & simulation — Seeded suspicious network")
      ).toBeTruthy()
    );
    expect(screen.getByLabelText("Replay controls")).toBeTruthy();
    expect(screen.getByLabelText("What-if simulation")).toBeTruthy();
    expect(
      (screen.getByLabelText("Target transaction") as HTMLInputElement).value
    ).toBe("txn_84721");
  });

  it("shows a not-found state for an unknown scenario", async () => {
    getReplayMock.mockRejectedValue(
      new ApiError("UNKNOWN_SCENARIO", "no scenario", 404, "t")
    );
    render(<ReplayPage />);
    await waitFor(() =>
      expect(screen.getByText("Scenario not found")).toBeTruthy()
    );
  });

  it("requires confirmation before reset and reports the result", async () => {
    resetDemoMock.mockResolvedValue({
      scenario_id: "scn_primary",
      run_id: "run_2",
      trace_id: "t",
      seed_hash: "abcdef0123456789",
      manifest: {},
    });
    render(<ReplayPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Reset demo" })).toBeTruthy()
    );
    fireEvent.click(screen.getByRole("button", { name: "Reset demo" }));
    expect(resetDemoMock).not.toHaveBeenCalled();
    expect(screen.getByText(/Confirm: this clears/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Confirm reset" }));
    await waitFor(() =>
      expect(screen.getByTestId("reset-result")).toHaveTextContent("run_2")
    );
    expect(resetDemoMock).toHaveBeenCalledWith("scn_primary");
  });

  it("cancel leaves state untouched", async () => {
    render(<ReplayPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Reset demo" })).toBeTruthy()
    );
    fireEvent.click(screen.getByRole("button", { name: "Reset demo" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(resetDemoMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/Confirm: this clears/)).toBeNull();
  });

  it("shows breadcrumbs with route params on every state", async () => {
    listScenariosMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    getReplayMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    render(<ReplayPage />);
    const nav = await screen.findByRole("navigation", { name: "Breadcrumb" });
    expect(nav.querySelector("a")?.getAttribute("href")).toBe("/demo");
    expect(
      within(nav).getByText("Replay scn_primary").getAttribute("aria-current")
    ).toBe("page");
  });
});

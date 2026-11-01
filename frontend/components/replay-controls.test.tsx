import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import type { ReplayState } from "../lib/api";
import { ReplayControls } from "./replay-controls";

const { getReplayMock } = vi.hoisted(() => ({ getReplayMock: vi.fn() }));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getReplay: getReplayMock,
}));

function stateFixture(cursor: number): ReplayState {
  return {
    scenario_id: "scn_primary",
    cursor,
    total: 2,
    current_event:
      cursor === 0
        ? null
        : {
            event_id: `evt_demo_8472${cursor}`,
            event_type: "financial.transaction.created",
            occurred_at: `2026-10-27T10:0${cursor}:00Z`,
            source: "synthetic_demo",
            trace_id: `trace_demo_8472${cursor}`,
            transaction: {
              transaction_id: `txn_8472${cursor}`,
              amount_minor: 48000000,
              currency: "NGN",
              channel: "MOBILE_APP",
              sender_account_id: "acct_A",
              receiver_account_id: "acct_B",
              occurred_at: `2026-10-27T10:0${cursor}:00Z`,
            },
            entities: {},
          },
    cumulative_event_ids: cursor === 0 ? [] : [`evt_demo_8472${cursor}`],
    cumulative_transaction_ids: cursor === 0 ? [] : [`txn_8472${cursor}`],
    cumulative_edge_ids: [],
    counts: { events: cursor, transactions: cursor === 0 ? 0 : 1, edges: 0 },
  };
}

beforeEach(() => {
  getReplayMock.mockReset();
  getReplayMock.mockImplementation(
    async (scenarioId: string, cursor: number) => stateFixture(cursor)
  );
});

describe("ReplayControls", () => {
  it("starts at step 0 and steps forward through server states", async () => {
    render(<ReplayControls scenarioId="scn_primary" />);
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 0 of 2"
      )
    );
    expect(
      screen.getByText(/no events applied yet/i)
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Step forward" }));
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 1 of 2"
      )
    );
    expect(getReplayMock).toHaveBeenLastCalledWith(
      "scn_primary",
      1,
      expect.anything()
    );
    expect(screen.getByTestId("replay-current")).toHaveTextContent(
      "evt_demo_84721"
    );
  });

  it("disables stepping past the end", async () => {
    render(<ReplayControls scenarioId="scn_primary" />);
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 0 of 2"
      )
    );
    fireEvent.click(screen.getByRole("button", { name: "Step forward" }));
    // The button is correctly disabled while the step loads; wait for
    // step 1 to render (button re-enabled) before stepping again.
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 1 of 2"
      )
    );
    fireEvent.click(screen.getByRole("button", { name: "Step forward" }));
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 2 of 2"
      )
    );
    expect(
      screen.getByRole("button", { name: "Step forward" })
    ).toHaveProperty("disabled", true);
  });

  it("shows an error with retry when the backend fails", async () => {
    getReplayMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<ReplayControls scenarioId="scn_primary" />);
    await waitFor(() =>
      expect(
        screen.getByText("BACKEND_UNREACHABLE: Failed to fetch")
      ).toBeTruthy()
    );
    getReplayMock.mockImplementation(async () => stateFixture(0));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(screen.getByTestId("replay-position")).toHaveTextContent(
        "Step 0 of 2"
      )
    );
  });
});

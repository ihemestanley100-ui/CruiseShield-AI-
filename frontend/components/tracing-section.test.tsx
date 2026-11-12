import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { FundTrace, TxnParties, Typology } from "../lib/api";
import { TracingSection } from "./tracing-section";

const { traceMock, getMock, partiesMock, typosMock } = vi.hoisted(() => ({
  traceMock: vi.fn(),
  getMock: vi.fn(),
  partiesMock: vi.fn(),
  typosMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  postTrace: traceMock,
  getTrace: getMock,
  getTxnParties: partiesMock,
  getTypologies: typosMock,
}));

beforeEach(() => {
  traceMock.mockReset();
  getMock.mockReset();
  partiesMock.mockReset();
  typosMock.mockReset();
});

function traceFixture(): FundTrace {
  return {
    trace_id: "trace_t1",
    origin_transaction: "t1",
    movements: [
      {
        from_transaction: "t1",
        to_transaction: "t2",
        hop: 1,
        status: "STRONGLY_SUPPORTED_LINK",
        evidence: "receiver->sender continuity in NGN",
        amount_minor: 1000,
        currency: "NGN",
      },
    ],
    visited_transactions: ["t1", "t2"],
    limitations: ["Hop limit reached; downstream movement unknown."],
    built_at: "2026-11-07T08:00:00Z",
  };
}

function partiesFixture(): TxnParties {
  return {
    transaction_id: "t1",
    parties: [
      {
        role: "SENDER",
        reference_masked: "a••1",
        label: null,
        source_field: "sender_account_id",
        verification: "UNVERIFIED",
      },
    ],
    classification: {
      method_id: "nip_instant",
      confidence: "inferred-from-channel",
      explanation: "hint",
    },
    network: {
      institution_id: "UNKNOWN",
      confidence: "unclassified",
      explanation: "none",
    },
    tenant_scope: "org_primary",
  };
}

function typoFixture(): Typology {
  return {
    typology_id: "T-25",
    label: "Suspicious gift-card redemption",
    detector_families: [],
    engine_rules: [],
    industries: ["retail"],
    industry_taxonomy_codes: [],
    detection_gap: true,
    mapping_errors: [],
  };
}

describe("TracingSection", () => {
  it("stays closed until expanded, then builds and shows the trace", async () => {
    traceMock.mockResolvedValue(traceFixture());
    getMock.mockResolvedValue(traceFixture());
    render(<TracingSection txnId="t1" />);
    expect(traceMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Build trace" }));
    await waitFor(() => expect(traceMock).toHaveBeenCalledWith("t1", 4));
    expect(await screen.findByText("STRONGLY_SUPPORTED_LINK")).toBeTruthy();
    expect(
      screen.getByText(/Hop limit reached/, { exact: false })
    ).toBeTruthy();
  });

  it("shows an empty movement list honestly", async () => {
    traceMock.mockResolvedValue({ ...traceFixture(), movements: [] });
    getMock.mockResolvedValue({ ...traceFixture(), movements: [] });
    render(<TracingSection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Build trace" }));
    expect(
      await screen.findByText("No evidenced onward movements.")
    ).toBeTruthy();
  });

  it("surfaces trace build errors", async () => {
    traceMock.mockRejectedValue(new Error("boom"));
    render(<TracingSection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Build trace" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });

  it("loads masked parties on demand", async () => {
    partiesMock.mockResolvedValue(partiesFixture());
    render(<TracingSection txnId="t1" />);
    expect(partiesMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Show parties" }));
    await waitFor(() => expect(partiesMock).toHaveBeenCalledWith("t1"));
    expect(await screen.findByText(/a••1/)).toBeTruthy();
  });

  it("flags detection-gap typologies", async () => {
    typosMock.mockResolvedValue({ typologies: [typoFixture()] });
    render(<TracingSection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Show typologies" }));
    expect(await screen.findByText("T-25")).toBeTruthy();
    expect(screen.getByText(/detection gap/)).toBeTruthy();
  });
});

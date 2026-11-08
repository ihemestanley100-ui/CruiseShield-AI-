import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RecoverySection } from "./recovery-section";

const { casesMock, metricsMock, assessMock, openMock } = vi.hoisted(() => ({
  casesMock: vi.fn(),
  metricsMock: vi.fn(),
  assessMock: vi.fn(),
  openMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getRecoveryCases: casesMock,
  getRecoveryMetrics: metricsMock,
  postRecoveryAssess: assessMock,
  postRecoveryCase: openMock,
}));

beforeEach(() => {
  casesMock.mockReset();
  metricsMock.mockReset();
  assessMock.mockReset();
  openMock.mockReset();
});

function queue() {
  casesMock.mockResolvedValue({ cases: [], tenant_scope: "org_primary" });
  metricsMock.mockResolvedValue({
    total: 0,
    by_state: {},
    by_reason: {},
    tenant_scope: "org_primary",
    window: "stored",
  });
}

describe("RecoverySection", () => {
  it("stays closed until expanded, then lists cases", async () => {
    queue();
    render(<RecoverySection txnId="t1" />);
    expect(casesMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Show recovery" }));
    await waitFor(() => expect(casesMock).toHaveBeenCalled());
    expect(await screen.findByText("0 case(s) recorded.")).toBeTruthy();
  });

  it("checks eligibility and renders the status verbatim", async () => {
    queue();
    assessMock.mockResolvedValue({
      status: "RULES_NOT_VERIFIED",
      rule_id: "TMPL-BANK-002",
      reason: "templates only",
      missing: ["verified-scheme-rule"],
      alternatives: ["historical-investigation"],
    });
    render(<RecoverySection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Show recovery" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Check eligibility" })
    );
    expect(await screen.findByText("RULES_NOT_VERIFIED")).toBeTruthy();
  });

  it("opens cases and reports duplicates honestly", async () => {
    queue();
    openMock.mockResolvedValue({
      status: "duplicate",
      case: {
        recovery_id: "recv_1",
        transaction_id: "t1",
        reason: "fraud",
        state: "CASE_CREATED",
        eligibility: null,
        evidence: [],
        channel: null,
        external_reference: null,
        history: [],
      },
    });
    render(<RecoverySection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Show recovery" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Open recovery case" })
    );
    expect(await screen.findByText("Case recv_1: duplicate.")).toBeTruthy();
  });

  it("surfaces load errors", async () => {
    casesMock.mockRejectedValue(new Error("down"));
    metricsMock.mockResolvedValue({
      total: 0,
      by_state: {},
      by_reason: {},
      tenant_scope: "org_primary",
      window: "stored",
    });
    render(<RecoverySection txnId="t1" />);
    fireEvent.click(screen.getByRole("button", { name: "Show recovery" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});

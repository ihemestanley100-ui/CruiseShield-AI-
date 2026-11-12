import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { FraudAlert, MonitoringStatus } from "../lib/api";
import { MonitoringSection } from "./monitoring-section";

const { statusMock, alertsMock, evalMock, openMock, moveMock } = vi.hoisted(
  () => ({
    statusMock: vi.fn(),
    alertsMock: vi.fn(),
    evalMock: vi.fn(),
    openMock: vi.fn(),
    moveMock: vi.fn(),
  })
);

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getMonitoringStatus: statusMock,
  getFraudAlerts: alertsMock,
  postMonitoringEvaluate: evalMock,
  postFraudAlert: openMock,
  patchFraudAlert: moveMock,
}));

beforeEach(() => {
  statusMock.mockReset();
  alertsMock.mockReset();
  evalMock.mockReset();
  openMock.mockReset();
  moveMock.mockReset();
});

function statusFixture(): MonitoringStatus {
  return {
    mode: "on-demand-evaluation",
    mode_note: "not streaming",
    tenant_scope: "org_primary",
    transactions_visible: 11,
    signals_visible: 4,
    alerts_open: 1,
    alerts_by_status: { NEW: 1 },
    signals_without_alerts: 3,
    data_window: { start: "2026-10-01T00:00:00Z", end: "2026-11-01T00:00:00Z" },
    computed_at: "2026-11-07T09:00:00Z",
  };
}

function alertFixture(): FraudAlert {
  return {
    id: "fraud_s1",
    signal_id: "s1",
    transaction_id: "t1",
    detector_family: "VELOCITY",
    severity: "high",
    status: "NEW",
    opened_at: "2026-11-07T09:00:00Z",
    history: [],
    notified: false,
  };
}

describe("MonitoringSection", () => {
  it("stays closed until expanded, then shows honest mode and counts", async () => {
    statusMock.mockResolvedValue(statusFixture());
    alertsMock.mockResolvedValue({ alerts: [], tenant_scope: "org_primary" });
    render(<MonitoringSection />);
    expect(statusMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Show monitoring" }));
    await waitFor(() => expect(statusMock).toHaveBeenCalled());
    expect(screen.getByText(/on-demand-evaluation/)).toBeTruthy();
    expect(screen.getByText(/No alerts recorded/)).toBeTruthy();
  });

  it("runs evaluation and reports opened versus duplicates", async () => {
    statusMock.mockResolvedValue(statusFixture());
    alertsMock.mockResolvedValue({ alerts: [], tenant_scope: "org_primary" });
    evalMock.mockResolvedValue({
      tenant_scope: "org_primary",
      signals_evaluated: 4,
      alerts_opened: ["fraud_s1"],
      alerts_duplicate: ["fraud_s2", "fraud_s3"],
      family_runs: {},
      family_errors: [],
      evaluated_at: "2026-11-07T09:00:00Z",
    });
    render(<MonitoringSection />);
    fireEvent.click(screen.getByRole("button", { name: "Show monitoring" }));
    fireEvent.click(await screen.findByRole("button", { name: "Run evaluation" }));
    expect(
      await screen.findByText("1 opened, 2 already tracked.")
    ).toBeTruthy();
  });

  it("offers only legal transitions per alert", async () => {
    statusMock.mockResolvedValue(statusFixture());
    alertsMock.mockResolvedValue({
      alerts: [alertFixture()],
      tenant_scope: "org_primary",
    });
    render(<MonitoringSection />);
    fireEvent.click(screen.getByRole("button", { name: "Show monitoring" }));
    await screen.findByText("fraud_s1");
    expect(screen.getByRole("button", { name: "TRIAGED" })).toBeTruthy();
    expect(
      screen.queryByRole("button", { name: "CLOSED" })
    ).toBeNull();
  });

  it("surfaces monitoring errors", async () => {
    statusMock.mockRejectedValue(new Error("down"));
    alertsMock.mockResolvedValue({ alerts: [], tenant_scope: "org_primary" });
    render(<MonitoringSection />);
    fireEvent.click(screen.getByRole("button", { name: "Show monitoring" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});

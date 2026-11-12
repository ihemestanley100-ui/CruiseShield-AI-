import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { HealthCheck } from "../lib/api";
import { SystemStatus } from "./system-status";

function healthFixture(checks: Record<string, string>): HealthCheck {
  return {
    status: "healthy",
    version: "1.0.0-p0",
    scenario_id: "scn_primary",
    run_id: "run_test",
    checks,
  };
}

describe("SystemStatus", () => {
  it("maps real checks to honest states", () => {
    render(
      <SystemStatus
        health={{
          ...healthFixture({
            store: "PASS",
            seed_integrity: "PASS",
            graph_provenance: "PASS",
            model_configured: "NOT_CONFIGURED",
          }),
          // A-1: unconfigured AI is operational_with_gaps, never
          // "healthy" — the old fixture encoded the defect.
          status: "operational_with_gaps",
        }}
        checkedAt="Oct 30, 2026"
      />
    );
    expect(screen.getByText("operational_with_gaps")).toBeTruthy();
    expect(
      screen.getByText("Operational with gaps: some services unconfigured")
    ).toBeTruthy();
    expect(screen.queryByText("All systems operational")).toBeNull();
    expect(screen.getByText("API Services")).toBeTruthy();
    expect(screen.getByText("AI Engine (Muse Spark)")).toBeTruthy();
    expect(screen.getByText("Not configured")).toBeTruthy();
    expect(screen.getByText("Scenario scn_primary", { exact: false })).toBeTruthy();
    expect(screen.getByText("run_test", { exact: false })).toBeTruthy();
    // UGLS-02: the timestamp sits in <bdi> (RTL isolation), so the
    // sentence spans two elements; textContent is unchanged.
    const stamp = screen.getByText("Oct 30, 2026");
    expect(stamp.tagName).toBe("BDI");
    expect(stamp.parentElement?.textContent).toBe("Checked Oct 30, 2026");
  });

  it("treats PASS with backend detail as operational and shows the detail", () => {
    render(
      <SystemStatus
        health={healthFixture({
          store: "PASS",
          seed_integrity: "PASS",
          graph_provenance: "PASS",
          model_configured: "NOT_CONFIGURED",
          storage_backend: "PASS active=json selected=json",
          pg: "NOT_CONFIGURED",
        })}
        checkedAt="now"
      />
    );
    // Display fix: machine keys render humanized ("Storage Backend").
    expect(screen.getByText("Storage Backend")).toBeTruthy();
    expect(screen.getByText("PG")).toBeTruthy();
    expect(
      screen.getByText("Operational: active=json selected=json", {
        exact: false,
      })
    ).toBeTruthy();
    expect(screen.queryByText("Degraded", { exact: false })).toBeNull();
  });

  it("keeps FAIL detail visible on degraded checks", () => {
    render(
      <SystemStatus
        health={{
          ...healthFixture({ store: "FAIL boom" }),
          status: "degraded",
        }}
        checkedAt="now"
      />
    );
    expect(
      screen.getByText("Degraded: boom", { exact: false })
    ).toBeTruthy();
  });

  it("reports degraded checks without hiding detail", () => {
    render(
      <SystemStatus
        health={{
          ...healthFixture({ store: "PASS" }),
          status: "degraded",
        }}
        checkedAt="now"
      />
    );
    expect(screen.getByText("degraded")).toBeTruthy();
    expect(screen.queryByText("All systems operational")).toBeNull();
    expect(
      screen.queryByText("Operational with gaps: some services unconfigured")
    ).toBeNull();
    expect(screen.getAllByText("Not reported").length).toBeGreaterThan(0);
  });

  it("reserves the all-operational headline for a fully healthy status", () => {
    render(
      <SystemStatus
        health={healthFixture({
          store: "PASS",
          seed_integrity: "PASS",
          graph_provenance: "PASS",
          model_configured: "PASS",
        })}
        checkedAt="now"
      />
    );
    expect(screen.getByText("All systems operational")).toBeTruthy();
    expect(
      screen.queryByText("Operational with gaps: some services unconfigured")
    ).toBeNull();
  });

  it("shows no positive headline when unavailable", () => {
    render(
      <SystemStatus
        health={{
          ...healthFixture({ store: "FAIL" }),
          status: "unavailable",
        }}
        checkedAt="now"
      />
    );
    expect(screen.getByText("unavailable")).toBeTruthy();
    expect(screen.queryByText("All systems operational")).toBeNull();
    expect(
      screen.queryByText("Operational with gaps: some services unconfigured")
    ).toBeNull();
  });
});

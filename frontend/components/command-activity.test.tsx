import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { AuditEntry } from "../lib/api";
import { CommandActivity } from "./command-activity";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function audit(n: number): AuditEntry {
  const id = `audit_${String(n).padStart(4, "0")}`;
  return {
    audit_event_id: id,
    actor_type: "service",
    actor_id: "seed",
    action: "demo.reset",
    target_type: "scenario",
    target_id: "case_84721",
    previous_state_reference: "",
    new_state_reference: "scn_primary",
    reason: "seeded scenario",
    timestamp: "2026-10-27T10:00:00Z",
    trace_id: "trace_demo_84721",
    request_id: `req_${n}`,
  };
}

describe("CommandActivity", () => {
  it("shows the latest entries with labelled truncation", () => {
    const audits = [1, 2, 3, 4, 5, 6, 7].map(audit);
    render(<CommandActivity audits={audits} caseId="case_84721" />);
    expect(screen.getByTestId("command-activity-counts").textContent).toContain(
      "7 audit events"
    );
    expect(screen.getByTestId("command-activity-counts").textContent).toContain(
      "showing latest 5"
    );
    expect(screen.queryByText("audit_0001")).toBeNull();
    expect(screen.queryByText("audit_0002")).toBeNull();
    expect(screen.getByText("audit_0007")).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: "Open case audit trail" })
        .getAttribute("href")
    ).toBe("/cases/case_84721/audit");
  });

  it("shows an honest empty state", () => {
    render(<CommandActivity audits={[]} caseId="case_84721" />);
    expect(screen.getByText("No audit events recorded yet.")).toBeTruthy();
  });
});

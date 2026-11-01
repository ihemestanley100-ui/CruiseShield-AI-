import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AuditEntry } from "../lib/api";
import { AuditList } from "./audit-list";

const AUDITS: AuditEntry[] = [
  {
    audit_event_id: "audit_0002",
    actor_type: "system",
    actor_id: "demo-reset",
    action: "case.opened",
    target_type: "case",
    target_id: "case_84721",
    previous_state_reference: "",
    new_state_reference: "NEW",
    reason: "Case opened for primary investigation",
    timestamp: "2026-10-28T00:00:00Z",
    trace_id: "t",
    request_id: "t",
  },
  {
    audit_event_id: "audit_0006",
    actor_type: "human",
    actor_id: "investigator",
    action: "case.decision",
    target_type: "case",
    target_id: "case_84721",
    previous_state_reference: "NEW",
    new_state_reference: "TRIAGED",
    reason: "Triage: confirmed network support.",
    timestamp: "2026-10-28T01:00:00Z",
    trace_id: "t",
    request_id: "t",
  },
];

describe("AuditList", () => {
  it("renders every entry with actor, change and reason", () => {
    const { container } = render(<AuditList audits={AUDITS} />);
    expect(screen.getByTestId("audit-counts")).toHaveTextContent(
      "2 audit events."
    );
    expect(container.querySelectorAll("[data-audit-row]")).toHaveLength(2);
    const row = container.querySelector('[data-audit-row="audit_0006"]');
    expect(row?.textContent).toContain("human/investigator");
    expect(row?.textContent).toContain("case.decision");
    expect(row?.textContent).toContain("TRIAGED");
    expect(row?.textContent).toContain("Triage: confirmed network support.");
  });

  it("shows a readable time while keeping full precision", () => {
    const { container } = render(<AuditList audits={AUDITS} />);
    const time = container.querySelector(
      '[data-audit-row="audit_0002"] time'
    );
    expect(time?.textContent).toBe("2026-10-28 00:00:00 UTC");
    expect(time?.getAttribute("dateTime")).toBe("2026-10-28T00:00:00Z");
    expect(time?.getAttribute("title")).toBe("2026-10-28T00:00:00Z");
  });

  it("renders unparseable timestamps verbatim", () => {
    const { container } = render(
      <AuditList
        audits={[{ ...AUDITS[0], timestamp: "not-a-time" }]}
      />
    );
    expect(
      container.querySelector("[data-audit-row] time")?.textContent
    ).toBe("not-a-time");
  });

  it("shows an empty message when no audits exist", () => {
    render(<AuditList audits={[]} />);
    expect(
      screen.getByText("No audit events recorded for this case.")
    ).toBeTruthy();
  });
});

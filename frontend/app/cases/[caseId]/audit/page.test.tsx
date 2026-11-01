import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../../lib/api";
import type { AuditEntry } from "../../../../lib/api";
import CaseAuditPage from "./page";

const { getCaseAuditMock } = vi.hoisted(() => ({
  getCaseAuditMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ caseId: "case_84721" }),
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

vi.mock("../../../../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getCaseAudit: getCaseAuditMock,
}));

function auditFixture(id: string): AuditEntry {
  return {
    audit_event_id: id,
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
  };
}

beforeEach(() => {
  getCaseAuditMock.mockReset();
});

describe("CaseAuditPage", () => {
  it("renders loading then the recorded audit events in order", async () => {
    getCaseAuditMock.mockResolvedValue({
      audits: [auditFixture("audit_0002"), auditFixture("audit_0006")],
    });
    const { container } = render(<CaseAuditPage />);
    expect(screen.getByText("Loading audit events…")).toBeTruthy();
    const rows = await screen.findAllByText(/audit_00/);
    expect(rows.length).toBeGreaterThan(0);
    const order = [...container.querySelectorAll("[data-audit-row]")].map(
      (row) => row.getAttribute("data-audit-row")
    );
    expect(order).toEqual(["audit_0002", "audit_0006"]);
    expect(screen.getByTestId("audit-counts")).toHaveTextContent(
      "2 audit events."
    );
  });

  it("shows the empty state when no audit events are recorded", async () => {
    getCaseAuditMock.mockResolvedValue({ audits: [] });
    render(<CaseAuditPage />);
    expect(
      await screen.findByText("No audit events recorded for this case.")
    ).toBeTruthy();
    expect(getCaseAuditMock).toHaveBeenCalledWith(
      "case_84721",
      expect.any(AbortSignal)
    );
  });

  it("shows an error card with retry when the backend fails", async () => {
    getCaseAuditMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<CaseAuditPage />);
    expect(await screen.findByText(/BACKEND_UNREACHABLE/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("shows a not-found panel for unknown cases", async () => {
    getCaseAuditMock.mockRejectedValue(
      new ApiError("CASE_NOT_FOUND", "case_999", 404, "")
    );
    render(<CaseAuditPage />);
    expect(await screen.findByText("Case not found")).toBeTruthy();
  });

  it("breadcrumbs link back through the parent case", async () => {
    getCaseAuditMock.mockResolvedValue({ audits: [] });
    render(<CaseAuditPage />);
    const nav = await screen.findByRole("navigation", { name: "Breadcrumb" });
    const links = [...nav.querySelectorAll("a")].map((a) =>
      a.getAttribute("href")
    );
    expect(links).toEqual(["/demo", "/cases/case_84721"]);
    expect(
      within(nav).getByText("Audit trail").getAttribute("aria-current")
    ).toBe("page");
    expect(
      screen.getByRole("link", { name: "Back to case" }).getAttribute("href")
    ).toBe("/cases/case_84721");
  });
});

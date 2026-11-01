import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, type AlertItem } from "../lib/api";
import { Notifications } from "./notifications";

const { listAlertsMock } = vi.hoisted(() => ({ listAlertsMock: vi.fn() }));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  listAlerts: listAlertsMock,
}));

function alertFixture(
  alert_id: string,
  status = "OPEN",
  transaction_id = "txn_84721"
): AlertItem {
  return {
    alert_id,
    transaction_id,
    title: `HIGH network risk: transaction #${alert_id.split("_")[1]}`,
    status,
    risk_assessment_id: "risk_network_84721",
    created_at: "2026-10-29T20:32:15Z",
    trace_id: "trace_run_test",
  };
}

beforeEach(() => {
  listAlertsMock.mockReset();
});

describe("Notifications", () => {
  it("badges the real open-alert count and lists genuine alerts", async () => {
    listAlertsMock.mockResolvedValue({
      alerts: [alertFixture("alert_84721"), alertFixture("alert_84730", "TRIAGED", "txn_84730")],
    });
    render(<Notifications />);
    const bell = await screen.findByRole("button", {
      name: "Notifications, 1 open",
    });
    expect(bell.textContent).toContain("1");
    fireEvent.click(bell);
    expect(
      screen.getByText("HIGH network risk: transaction #84721")
    ).toBeTruthy();
    const invLinks = screen.getAllByRole("link", {
      name: "Open investigation",
    });
    expect(invLinks.map((a) => a.getAttribute("href"))).toEqual([
      "/investigations/inv_84721",
      "/investigations/inv_84730",
    ]);
    const networkLinks = screen.getAllByRole("link", { name: "Network" });
    expect(networkLinks[0].getAttribute("href")).toBe("/network/txn_84721");
    expect(networkLinks[1].getAttribute("href")).toBe("/network/txn_84730");
  });

  it("shows loading, empty, and error states honestly", async () => {
    listAlertsMock.mockReturnValue(new Promise(() => {}));
    const { unmount } = render(<Notifications />);
    fireEvent.click(screen.getByRole("button", { name: "Notifications, loading" }));
    expect(screen.getByText("Loading alerts…")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Notifications, loading" })
    ).toBeTruthy();
    unmount();

    listAlertsMock.mockResolvedValue({ alerts: [] });
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 0 open" })
    );
    expect(screen.getByText("No alerts.")).toBeTruthy();
  });

  it("shows backend errors without inventing alerts", async () => {
    listAlertsMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 0 open" })
    );
    expect(screen.getByRole("alert").textContent).toContain(
      "BACKEND_UNREACHABLE: Failed to fetch"
    );
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("closes on Escape and returns focus to the bell", async () => {
    listAlertsMock.mockResolvedValue({ alerts: [alertFixture("alert_84721")] });
    render(<Notifications />);
    const bell = await screen.findByRole("button", {
      name: "Notifications, 1 open",
    });
    fireEvent.click(bell);
    expect(
      screen.getByRole("dialog", { name: "Notifications" })
    ).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).toBeNull()
    );
    expect(document.activeElement).toBe(bell);
  });

  it("links unknown alert shapes to the network only, never a guess", async () => {
    listAlertsMock.mockResolvedValue({
      alerts: [alertFixture("weird-id", "OPEN", "txn_84721")],
    });
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 1 open" })
    );
    expect(screen.queryByRole("link", { name: "Open investigation" })).toBeNull();
    expect(
      screen.getByRole("link", { name: "Network" }).getAttribute("href")
    ).toBe("/network/txn_84721");
  });
});

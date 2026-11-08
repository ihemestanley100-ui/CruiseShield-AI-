import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, type NotificationItem } from "../lib/api";
import { Notifications } from "./notifications";

const { listMock, markMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  markMock: vi.fn(),
}));

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
  listNotifications: listMock,
  markNotificationsRead: markMock,
}));

function itemFixture(
  notification_id: string,
  status = "OPEN",
  read = false,
  transaction_id: string | null = "txn_84721"
): NotificationItem {
  return {
    notification_id,
    transaction_id,
    title: `HIGH network risk: transaction #${notification_id.split("_")[1]}`,
    status,
    created_at: "2026-10-29T20:32:15Z",
    read,
  };
}

function listFixture(items: NotificationItem[]) {
  const unread = items.filter((n) => !n.read && n.status === "OPEN").length;
  return {
    notifications: items,
    unread_count: unread,
    synthetic_notice: "Synthetic data.",
  };
}

beforeEach(() => {
  listMock.mockReset();
  markMock.mockReset();
});

describe("Notifications", () => {
  it("badges the backend unread count and lists genuine items", async () => {
    listMock.mockResolvedValue(
      listFixture([
        itemFixture("alert_84721"),
        itemFixture("alert_84730", "TRIAGED", false, "txn_84730"),
      ])
    );
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
    listMock.mockReturnValue(new Promise(() => {}));
    const { unmount } = render(<Notifications />);
    fireEvent.click(screen.getByRole("button", { name: "Notifications, loading" }));
    expect(screen.getByText("Loading alerts…")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Notifications, loading" })
    ).toBeTruthy();
    unmount();

    listMock.mockResolvedValue(listFixture([]));
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 0 open" })
    );
    expect(screen.getByText("No alerts.")).toBeTruthy();
  });

  it("shows backend errors without inventing items", async () => {
    listMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 0 open" })
    );
    expect(screen.getByRole("alert").textContent).toContain(
      "Backend unreachable. Check the platform server and retry."
    );
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("marks one item read and updates the badge from the server count", async () => {
    listMock.mockResolvedValue(listFixture([itemFixture("alert_84721")]));
    markMock.mockResolvedValue({ marked: ["alert_84721"], unread_count: 0 });
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 1 open" })
    );
    fireEvent.click(screen.getByRole("button", { name: "Mark read" }));
    await waitFor(() =>
      expect(markMock).toHaveBeenCalledWith({
        notification_ids: ["alert_84721"],
      })
    );
    await screen.findByRole("button", { name: "Notifications, 0 open" });
    expect(
      screen.queryByRole("button", { name: "Mark read" })
    ).toBeNull();
  });

  it("marks all read and refreshes from the backend", async () => {
    listMock.mockResolvedValue(
      listFixture([itemFixture("alert_84721"), itemFixture("alert_84730")])
    );
    markMock.mockResolvedValue({
      marked: ["alert_84721", "alert_84730"],
      unread_count: 0,
    });
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 2 open" })
    );
    fireEvent.click(screen.getByRole("button", { name: "Mark all read" }));
    await waitFor(() => expect(markMock).toHaveBeenCalledWith({ all: true }));
    await screen.findByRole("button", { name: "Notifications, 0 open" });
    const calls = listMock.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(listMock.mock.calls.length).toBeGreaterThan(calls)
    );
  });

  it("surfaces mark-read failures without losing the list", async () => {
    listMock.mockResolvedValue(listFixture([itemFixture("alert_84721")]));
    markMock.mockRejectedValue(
      new ApiError("WRITE_TOKEN_REQUIRED", "denied", 401, "")
    );
    render(<Notifications />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Notifications, 1 open" })
    );
    fireEvent.click(screen.getByRole("button", { name: "Mark read" }));
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain(
        "Not available for your role."
      )
    );
  });

  it("closes on Escape and returns focus to the bell", async () => {
    listMock.mockResolvedValue(listFixture([itemFixture("alert_84721")]));
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

  it("links unknown shapes to the network only, never a guess", async () => {
    listMock.mockResolvedValue(
      listFixture([itemFixture("weird-id", "OPEN", false, "txn_84721")])
    );
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

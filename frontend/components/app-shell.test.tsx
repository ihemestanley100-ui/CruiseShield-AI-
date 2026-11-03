import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import { AppShell } from "./app-shell";

const {
  usePathnameMock,
  listAlertsMock,
  modeMock,
  meMock,
  loginMock,
  logoutMock,
} = vi.hoisted(() => ({
  usePathnameMock: vi.fn(() => "/demo"),
  listAlertsMock: vi.fn(),
  modeMock: vi.fn(),
  meMock: vi.fn(),
  loginMock: vi.fn(),
  logoutMock: vi.fn(),
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

vi.mock("next/navigation", () => ({
  usePathname: () => usePathnameMock(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  listAlerts: listAlertsMock,
  getAuthMode: modeMock,
  getAuthMe: meMock,
  postLogin: loginMock,
  postLogout: logoutMock,
}));

beforeEach(() => {
  usePathnameMock.mockReset();
  usePathnameMock.mockReturnValue("/demo");
  listAlertsMock.mockReset();
  listAlertsMock.mockResolvedValue({ alerts: [] });
  modeMock.mockReset();
  meMock.mockReset();
  loginMock.mockReset();
  logoutMock.mockReset();
  // No backend in shell tests: fail open exactly like production local demo.
  modeMock.mockRejectedValue(new ApiError("BACKEND_UNREACHABLE", "down", 0, ""));
  logoutMock.mockResolvedValue({ ok: true });
});

describe("AppShell", () => {
  /* Checking-first gate: full-shell tests await resolution (fail-open
   * demo resolves on the mocked mode rejection). */
  async function renderResolved(children: React.ReactNode) {
    const result = render(<AppShell>{children}</AppShell>);
    await screen.findByText("child");
    return result;
  }

  it("keeps headings out of the shell chrome (page h1 stays first)", async () => {
    const { container } = await renderResolved(<p>child</p>);
    expect(container.querySelectorAll("h1,h2,h3,h4,h5,h6")).toHaveLength(0);
    expect(screen.getByText("Quick Actions").tagName).toBe("P");
  });

  it("renders brand, theme, disclosure, and demo profile", async () => {
    await renderResolved(<p>child</p>);
    expect(screen.getByText("CruiseShield AI")).toBeTruthy();
    expect(
      screen.getByRole("radiogroup", { name: "Appearance" })
    ).toBeTruthy();
    expect(screen.getByText("Synthetic demo data")).toBeTruthy();
    expect(screen.getByText("Investigator")).toBeTruthy();
    expect(screen.getByText("demo role")).toBeTruthy();
    expect(screen.getByText("child")).toBeTruthy();
  });

  it("uses the official logo asset for the shell brand", () => {
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    const logo = screen.getByAltText("CruiseShield AI official shield logo");
    expect(logo.getAttribute("src")).toBe(
      "/assets/cruiseshield-logo-original.png"
    );
  });

  it("makes logo and brand name one home link", () => {
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    const home = screen.getByRole("link", { name: "CruiseShield AI home" });
    expect(home.getAttribute("href")).toBe("/");
    // Logo and brand text both live inside the same anchor.
    const logo = screen.getByAltText("CruiseShield AI official shield logo");
    expect(logo.closest("a")).toBe(home);
    expect(home.textContent).toContain("CruiseShield AI");
    expect(home.textContent).toContain("Financial Crime Immune System™");
  });

  it("links only real destinations and marks the active page", async () => {
    await renderResolved(<p>child</p>);
    const nav = screen.getByRole("navigation", { name: "Primary" });
    const hrefs = [...nav.querySelectorAll("a")].map((a) =>
      a.getAttribute("href")
    );
    expect(hrefs).toEqual([
      "/demo",
      "/investigations/inv_84721",
      "/cases/case_84721",
      "/network/txn_84721",
      "/replay/scn_primary",
      "/investigations/inv_84721#evidence-h",
      "/investigations/inv_84721#ai-h",
      "/cases/case_84721/audit",
    ]);
    expect(
      screen
        .getByRole("link", { name: "Command Center" })
        .getAttribute("aria-current")
    ).toBe("page");
  });

  it("renders navigation without duplicate React keys (F-001)", () => {
    const errors: string[] = [];
    const spy = vi
      .spyOn(console, "error")
      .mockImplementation((...args: unknown[]) => {
        errors.push(args.map(String).join(" "));
      });
    try {
      render(
        <AppShell>
          <p>child</p>
        </AppShell>
      );
    } finally {
      spy.mockRestore();
    }
    expect(errors.filter((m) => m.includes("same key"))).toEqual([]);
  });

  it("renders the landing full-bleed without shell chrome", () => {
    usePathnameMock.mockReturnValue("/");
    const { container } = render(
      <AppShell>
        <p>landing</p>
      </AppShell>
    );
    expect(screen.getByText("landing")).toBeTruthy();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(
      container.querySelector(".landing-shell")
    ).toBeTruthy();
  });

  it("toggles the drawer and closes on Escape", async () => {
    await renderResolved(<p>child</p>);
    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
  });

  it("moves focus into the drawer and back to the toggle", async () => {
    const { container } = await renderResolved(<p>child</p>);
    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    const drawer = container.querySelector("#app-sidebar") as HTMLElement;
    fireEvent.click(toggle);
    expect(document.activeElement).toBe(drawer);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(document.activeElement).toBe(toggle);
  });

  it("locks background scroll while the drawer is open", async () => {
    await renderResolved(<p>child</p>);
    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    fireEvent.click(toggle);
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(document.body.style.overflow).toBe("");
  });

  it("closes the drawer from the overlay and on route change", async () => {
    const { rerender } = await renderResolved(<p>child</p>);
    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    fireEvent.click(toggle);
    fireEvent.click(screen.getByRole("button", { name: "Close navigation" }));
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    usePathnameMock.mockReturnValue("/network/txn_84721");
    rerender(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
  });

  it("offers a skip link to the main landmark", async () => {
    const { container } = await renderResolved(<p>child</p>);
    const link = screen.getByRole("link", { name: "Skip to main content" });
    expect(link.getAttribute("href")).toBe("#main-content");
    expect(container.querySelector(".app-shell > :first-child")).toBe(link);
    const main = container.querySelector("main#main-content");
    expect(main?.getAttribute("tabindex")).toBe("-1");
  });

  it("withholds routes and fetches while checking the session", () => {
    modeMock.mockReturnValue(new Promise(() => {}));
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    expect(screen.getByText("Loading…").getAttribute("role")).toBe(
      "status"
    );
    expect(screen.queryByText("child")).toBeNull();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(
      screen.queryByRole("heading", { name: "Demo sign in" })
    ).toBeNull();
  });

  it("shows the sign-in gate when login is armed and logged out", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockRejectedValue(
      new ApiError("LOGIN_REQUIRED", "demo login required", 401, "")
    );
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    await screen.findByRole("heading", { name: "Demo sign in" });
    expect(screen.queryByText("child")).toBeNull();
    expect(screen.queryByRole("navigation")).toBeNull();
    // Brand home link still works from the gate.
    expect(
      screen.getByRole("link", { name: "CruiseShield AI home" })
    ).toBeTruthy();
  });

  it("shows the session user and signs out from the profile", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockResolvedValue({
      user: "judge",
      role: "investigator",
      permissions: ["read", "audit_read", "ai_run", "write"],
    });
    loginMock.mockResolvedValue({
      user: "judge",
      role: "investigator",
      permissions: ["read", "audit_read", "ai_run", "write"],
    });
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    await screen.findByRole("button", { name: "Sign out" });
    expect(screen.getByText("judge")).toBeTruthy();
    expect(screen.getByText("investigator · demo")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    await screen.findByRole("heading", { name: "Demo sign in" });
    expect(logoutMock).toHaveBeenCalled();
  });

  it("never gates the landing page, even when login is armed", async () => {
    usePathnameMock.mockReturnValue("/");
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockRejectedValue(
      new ApiError("LOGIN_REQUIRED", "demo login required", 401, "")
    );
    render(
      <AppShell>
        <p>landing</p>
      </AppShell>
    );
    expect(screen.getByText("landing")).toBeTruthy();
    await vi.waitFor(() => expect(modeMock).toHaveBeenCalled());
    expect(
      screen.queryByRole("heading", { name: "Demo sign in" })
    ).toBeNull();
  });

  it("badges the bell with the real open-alert count", async () => {
    listAlertsMock.mockResolvedValue({
      alerts: [
        {
          alert_id: "alert_84721",
          transaction_id: "txn_84721",
          title: "t",
          status: "OPEN",
          risk_assessment_id: "r",
          created_at: "2026-10-29T20:32:15Z",
          trace_id: "t",
        },
      ],
    });
    render(
      <AppShell>
        <p>child</p>
      </AppShell>
    );
    const bell = await screen.findByRole("button", {
      name: "Notifications, 1 open",
    });
    expect(bell.textContent).toContain("1");
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import { LoginCard, useDemoSession } from "./login-gate";

const { modeMock, meMock, loginMock, logoutMock } = vi.hoisted(() => ({
  modeMock: vi.fn(),
  meMock: vi.fn(),
  loginMock: vi.fn(),
  logoutMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getAuthMode: modeMock,
  getAuthMe: meMock,
  postLogin: loginMock,
  postLogout: logoutMock,
}));

/* Same usage shape as AppShell: gate swaps children for the card. */
function Harness({ children }: { children: React.ReactNode }) {
  const { gate, login, logout } = useDemoSession();
  if (gate.status === "login") return <LoginCard onLogin={login} />;
  return (
    <>
      {children}
      {gate.status === "authed" && (
        <button type="button" onClick={() => void logout()}>
          out
        </button>
      )}
    </>
  );
}

function auth401() {
  return new ApiError("LOGIN_REQUIRED", "demo login required", 401, "");
}

beforeEach(() => {
  modeMock.mockReset();
  meMock.mockReset();
  loginMock.mockReset();
  logoutMock.mockReset();
  logoutMock.mockResolvedValue({ ok: true });
});

describe("useDemoSession", () => {
  it("renders children directly when auth is disabled", async () => {
    modeMock.mockResolvedValue({ auth_enabled: false });
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    expect(screen.getByText("child")).toBeTruthy();
    expect(
      screen.queryByRole("heading", { name: "Demo sign in" })
    ).toBeNull();
    expect(meMock).not.toHaveBeenCalled();
  });

  it("fails open when the backend is unreachable", async () => {
    modeMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "down", 0, "")
    );
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    expect(screen.getByText("child")).toBeTruthy();
    await vi.waitFor(() => expect(modeMock).toHaveBeenCalled());
    expect(
      screen.queryByRole("heading", { name: "Demo sign in" })
    ).toBeNull();
  });

  it("gates children behind login when armed and logged out", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockRejectedValue(auth401());
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    await screen.findByRole("heading", { name: "Demo sign in" });
    expect(screen.queryByText("child")).toBeNull();
  });

  it("restores the session when a valid cookie exists", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockResolvedValue({ user: "judge", role: "investigator" });
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    await screen.findByText("child");
    expect(
      screen.queryByRole("heading", { name: "Demo sign in" })
    ).toBeNull();
    expect(await screen.findByRole("button", { name: "out" })).toBeTruthy();
  });

  it("signs in through the form and signs out again", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockRejectedValue(auth401());
    loginMock.mockResolvedValue({ user: "judge", role: "admin" });
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    await screen.findByRole("heading", { name: "Demo sign in" });
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "  judge " },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "s3cret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByText("child");
    expect(loginMock).toHaveBeenCalledWith("judge", "s3cret");
    fireEvent.click(screen.getByRole("button", { name: "out" }));
    await screen.findByRole("heading", { name: "Demo sign in" });
    expect(logoutMock).toHaveBeenCalled();
  });
});

describe("LoginCard", () => {
  it("shows an inline error when login fails", async () => {
    const onLogin = vi.fn().mockResolvedValue("Invalid username or password.");
    render(<LoginCard onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "judge" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByRole("alert");
    expect(screen.getByRole("alert").textContent).toBe(
      "Invalid username or password."
    );
  });

  it("maps rate limits and unreachable backends to guidance", async () => {
    modeMock.mockResolvedValue({ auth_enabled: true });
    meMock.mockRejectedValue(auth401());
    loginMock.mockRejectedValueOnce(
      new ApiError("LOGIN_RATE_LIMITED", "slow down", 429, "")
    );
    loginMock.mockRejectedValueOnce(
      new ApiError("BACKEND_UNREACHABLE", "down", 0, "")
    );
    render(
      <Harness>
        <p>child</p>
      </Harness>
    );
    await screen.findByRole("heading", { name: "Demo sign in" });
    const user = screen.getByLabelText("Username");
    const pass = screen.getByLabelText("Password");
    const submit = screen.getByRole("button", { name: "Sign in" });
    fireEvent.change(user, { target: { value: "judge" } });
    fireEvent.change(pass, { target: { value: "x" } });
    fireEvent.click(submit);
    await screen.findByText(/Too many login attempts/);
    fireEvent.click(submit);
    await screen.findByText(/Backend unreachable/);
  });

  it("disables submit while a login is in flight", async () => {
    let release!: (v: string | null) => void;
    const pending = new Promise<string | null>((res) => {
      release = res;
    });
    render(<LoginCard onLogin={() => pending} />);
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "judge" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "x" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(
      screen.getByRole("button", { name: "Signing in…" })
    ).toHaveAttribute("disabled");
    release(null);
    await screen.findByRole("button", { name: "Sign in" });
  });
});

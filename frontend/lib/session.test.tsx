import { beforeEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { publishSession, useCan } from "./session";

function Probe({ permission }: { permission: string }) {
  return <span data-testid="probe">{useCan(permission) ? "yes" : "no"}</span>;
}

const INVESTIGATOR = {
  user: "judge",
  role: "investigator",
  permissions: ["read", "audit_read", "ai_run", "write"],
};
const VIEWER = {
  user: "vie",
  role: "demo_viewer",
  permissions: ["read"],
};

describe("session store and useCan", () => {
  beforeEach(() => {
    publishSession({ mode: "open" });
  });

  it("enables everything in open-demo mode", () => {
    render(<Probe permission="write" />);
    expect(screen.getByTestId("probe").textContent).toBe("yes");
  });

  it("denies everything at the login gate", () => {
    publishSession({ mode: "login" });
    render(<Probe permission="read" />);
    expect(screen.getByTestId("probe").textContent).toBe("no");
  });

  it("follows the authed role permission set", () => {
    publishSession({ mode: "authed", session: INVESTIGATOR });
    const { rerender } = render(<Probe permission="write" />);
    expect(screen.getByTestId("probe").textContent).toBe("yes");
    publishSession({ mode: "authed", session: VIEWER });
    rerender(<Probe permission="write" />);
    expect(screen.getByTestId("probe").textContent).toBe("no");
    rerender(<Probe permission="read" />);
    expect(screen.getByTestId("probe").textContent).toBe("yes");
  });
});

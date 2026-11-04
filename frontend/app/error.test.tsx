import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RouteError from "./error";

describe("route error boundary", () => {
  it("offers retry and shows the digest ref", () => {
    const reset = vi.fn();
    render(<RouteError error={Object.assign(new globalThis.Error("boom"), { digest: "abc123" })} reset={reset} />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText(/ref abc123/)).toBeTruthy();
    fireEvent.click(screen.getByText("Try again"));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("renders without a digest", () => {
    render(<RouteError error={new globalThis.Error("boom")} reset={() => {}} />);
    expect(screen.getByText("Try again")).toBeTruthy();
  });
});

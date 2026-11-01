import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RiskBadge } from "./risk-badge";

afterEach(() => {
  vi.useRealTimers();
});

describe("RiskBadge", () => {
  it("announces the exact score while animating to it", () => {
    vi.useFakeTimers();
    render(<RiskBadge score={84} band="HIGH" />);
    expect(
      screen.getByLabelText("Risk 84 of 100, HIGH")
    ).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("risk-gauge")).toBeTruthy();
  });

  it("grounds the gauge width in the actual score", () => {
    vi.useFakeTimers();
    const { container } = render(<RiskBadge score={35} band="MODERATE" />);
    const fill = container.querySelector(".risk-gauge-fill");
    expect(fill?.getAttribute("style")).toContain("width: 35%");
  });
});

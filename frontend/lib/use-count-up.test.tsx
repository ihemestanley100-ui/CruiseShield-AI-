import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useCountUp } from "./use-count-up";

function Probe({ value }: { value: number }) {
  return <span data-testid="n">{useCountUp(value)}</span>;
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useCountUp", () => {
  it("converges to the exact application value", () => {
    vi.useFakeTimers();
    render(<Probe value={84} />);
    expect(screen.getByTestId("n")).toHaveTextContent("0");
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("n")).toHaveTextContent("84");
  });

  it("returns the final value immediately for reduced motion", () => {
    // stubGlobal (removed by unstubAllGlobals): defineProperty + global
    // restore leaves a neutered mock that returns undefined.
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query === "(prefers-reduced-motion: reduce)",
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }))
    );
    const raf = vi.spyOn(window, "requestAnimationFrame");
    render(<Probe value={84} />);
    expect(screen.getByTestId("n")).toHaveTextContent("84");
    expect(raf).not.toHaveBeenCalled();
  });

  it("never renders a negative count when a frame predates start", () => {
    vi.useFakeTimers();
    // Mixed clocks: the first rAF timestamp arrives earlier than the
    // performance.now() captured at effect start.
    const realRaf = window.requestAnimationFrame.bind(window);
    let first = true;
    vi.stubGlobal(
      "requestAnimationFrame",
      vi.fn().mockImplementation((cb: FrameRequestCallback) => {
        if (first) {
          first = false;
          cb(performance.now() - 500);
          return 1;
        }
        return realRaf(cb);
      })
    );
    render(<Probe value={84} />);
    expect(screen.getByTestId("n")).toHaveTextContent("0");
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("n")).toHaveTextContent("84");
  });

  it("tracks value changes without exceeding them", () => {
    vi.useFakeTimers();
    const { rerender } = render(<Probe value={35} />);
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("n")).toHaveTextContent("35");
    rerender(<Probe value={84} />);
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("n")).toHaveTextContent("84");
  });
});

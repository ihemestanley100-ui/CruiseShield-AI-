import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AmbientBackground } from "./ambient-background";

function ctxStub() {
  return {
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    setTransform: vi.fn(),
    set strokeStyle(_v: string) {},
    set fillStyle(_v: string) {},
    set lineWidth(_v: number) {},
  } as unknown as CanvasRenderingContext2D;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("AmbientBackground", () => {
  it("is decorative and non-interactive", () => {
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
    render(<AmbientBackground />);
    const canvas = screen.getByTestId("ambient-background");
    expect(canvas.getAttribute("aria-hidden")).toBe("true");
    expect(canvas.className).toContain("ambient-canvas");
  });

  it("renders nothing animated when canvas 2D is unavailable", () => {
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
    const raf = vi.spyOn(window, "requestAnimationFrame");
    render(<AmbientBackground />);
    expect(raf).not.toHaveBeenCalled();
  });

  it("paints one static frame under reduced motion", () => {
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
    const ctx = ctxStub();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(ctx);
    const raf = vi.spyOn(window, "requestAnimationFrame");
    render(<AmbientBackground />);
    expect(ctx.clearRect).toHaveBeenCalled();
    expect(raf).not.toHaveBeenCalled();
  });

  it("cleans up animation and listeners on unmount", () => {
    const ctx = ctxStub();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(ctx);
    const cancel = vi.spyOn(window, "cancelAnimationFrame");
    const remove = vi.spyOn(document, "removeEventListener");
    const { unmount } = render(<AmbientBackground />);
    unmount();
    expect(cancel).toHaveBeenCalled();
    expect(remove).toHaveBeenCalledWith(
      "visibilitychange",
      expect.any(Function)
    );
  });
});

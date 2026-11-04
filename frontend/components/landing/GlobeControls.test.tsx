import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GlobeControls } from "./GlobeControls";
import { GlobeController } from "./scene/controls";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("GlobeControls", () => {
  it("dispatches zoom and reset through the shared controller", () => {
    const controller = new GlobeController();
    render(<GlobeControls controller={controller} />);
    fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(controller.getState().zoom).toBeLessThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Zoom out" }));
    expect(controller.getState().zoom).toBeCloseTo(0, 9);
    controller.zoomBy(1);
    fireEvent.click(screen.getByRole("button", { name: "Reset view" }));
    expect(controller.getState().zoom).toBe(0);
  });

  it("shows the selected region with an illustrative-data note", () => {
    const controller = new GlobeController();
    render(<GlobeControls controller={controller} />);
    expect(screen.queryByRole("status")).toBeNull();
    act(() => controller.select(2));
    expect(screen.getByRole("status").textContent).toContain("Europe");
    expect(screen.getByRole("status").textContent).toContain(
      "Illustrative signal"
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Clear region selection" })
    );
    expect(controller.getState().selected).toBe(-1);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("exposes keyboard instructions to assistive technology", () => {
    render(<GlobeControls controller={new GlobeController()} />);
    expect(screen.getByText(/Drag to rotate/)).toBeTruthy();
  });
});

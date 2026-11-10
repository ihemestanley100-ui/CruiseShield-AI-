import { render, screen } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GlobalHeroScene } from "./GlobalHeroScene";
import { GlobeController } from "./scene/controls";

const { stats } = vi.hoisted(() => ({
  stats: { renderersCreated: 0, renderersDisposed: 0 },
}));

vi.mock("./scene/webgl", () => ({
  isWebGLAvailable: () => true,
  isPageVisible: () => true,
}));

// Fail AFTER renderer creation so the L-01 setup-path guard (not the
// renderer-construction guard) handles both StrictMode attempts.
vi.mock("./scene/earth", () => ({
  buildEarth: () => {
    throw new Error("simulated scene-setup failure");
  },
  EARTH_RADIUS: 1,
  REGION_HUBS: [],
}));

vi.mock("three", async (importOriginal) => {
  const actual = await importOriginal<typeof import("three")>();
  return {
    ...actual,
    WebGLRenderer: vi.fn(() => {
      stats.renderersCreated += 1;
      return {
        domElement: document.createElement("canvas"),
        setClearColor: vi.fn(),
        setPixelRatio: vi.fn(),
        setSize: vi.fn(),
        render: vi.fn(),
        dispose: () => {
          stats.renderersDisposed += 1;
        },
      };
    }),
  };
});

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

// Event types the hero scene attaches (window-level and canvas-level).
const SCENE_EVENT_TYPES = new Set([
  "resize",
  "pointermove",
  "visibilitychange",
  "pointerdown",
  "pointerup",
  "pointercancel",
  "wheel",
  "webglcontextlost",
  "webglcontextrestored",
]);

describe("GlobalHeroScene StrictMode double-mount (L-01)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("disposes every failed attempt and leaves zero resources", () => {
    const added: string[] = [];
    const rafCalls: number[] = [];
    vi.spyOn(window, "addEventListener").mockImplementation(
      ((type: string, ...rest: unknown[]) => {
        if (SCENE_EVENT_TYPES.has(type)) added.push(`window:${type}`);
        return undefined;
      }) as typeof window.addEventListener
    );
    vi.spyOn(HTMLCanvasElement.prototype, "addEventListener").mockImplementation(
      ((type: string, ...rest: unknown[]) => {
        if (SCENE_EVENT_TYPES.has(type)) added.push(`canvas:${type}`);
        return undefined;
      }) as unknown as typeof HTMLCanvasElement.prototype.addEventListener
    );
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((((
      callback: FrameRequestCallback
    ) => {
      rafCalls.push(1);
      return rafCalls.length;
    }) as unknown) as typeof window.requestAnimationFrame);

    const { container, unmount } = render(
      <StrictMode>
        <GlobalHeroScene
          motion="full"
          paused={false}
          controller={new GlobeController()}
        />
      </StrictMode>
    );

    // StrictMode runs setup → (no-op cleanup) → setup: two independent
    // failed attempts, each creating then releasing its own renderer.
    expect(stats.renderersCreated).toBe(2);
    expect(stats.renderersDisposed).toBe(2);
    // Both canvases removed; branded fallback takes over.
    expect(container.querySelectorAll("canvas")).toHaveLength(0);
    expect(screen.getByTestId("webgl-fallback")).toBeTruthy();
    // The setup throw precedes every attachment: no listeners, no frames.
    expect(added).toEqual([]);
    expect(rafCalls).toHaveLength(0);

    unmount();
    expect(container.querySelectorAll("canvas")).toHaveLength(0);
    expect(container.textContent).toBe("");
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GlobalHeroScene } from "./GlobalHeroScene";
import { GlobeController } from "./scene/controls";

const { disposeMock } = vi.hoisted(() => ({
  disposeMock: vi.fn(),
}));

vi.mock("./scene/webgl", () => ({
  isWebGLAvailable: () => true,
  isPageVisible: () => true,
}));

// L-01: fail AFTER renderer creation so the setup-path guard (not the
// pre-existing renderer-construction guard) is the handler under test.
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
    WebGLRenderer: vi.fn(() => ({
      domElement: document.createElement("canvas"),
      setClearColor: vi.fn(),
      setPixelRatio: vi.fn(),
      setSize: vi.fn(),
      render: vi.fn(),
      dispose: disposeMock,
    })),
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

describe("GlobalHeroScene setup failure (L-01)", () => {
  it("renders the branded fallback and releases the canvas when scene setup throws", () => {
    const { container } = render(
      <GlobalHeroScene
        motion="full"
        paused={false}
        controller={new GlobeController()}
      />
    );
    // The legacy renderer-construction guard never disposes: a dispose
    // call proves the new setup-path guard ran.
    expect(disposeMock).toHaveBeenCalled();
    expect(screen.getByTestId("webgl-fallback")).toBeTruthy();
    expect(container.querySelector("canvas")).toBeNull();
  });
});

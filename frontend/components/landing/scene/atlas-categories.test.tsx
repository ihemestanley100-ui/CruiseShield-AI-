import { render, screen } from "@testing-library/react";
import * as THREE from "three";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GlobeControls } from "../GlobeControls";
import { GlobalHeroScene } from "../GlobalHeroScene";
import {
  ATLAS_CATEGORIES,
  CORRIDOR_ROUTES,
  OCEAN_MARKER,
  isValidGeo,
} from "./categories";
import { GlobeController } from "./controls";
import { buildCorridorGroup } from "./corridors";
import { buildEarth, EARTH_RADIUS, REGION_HUBS } from "./earth";
import { makeLabelSprite } from "./shared";

vi.mock("./webgl", () => ({
  isWebGLAvailable: () => true,
  isPageVisible: () => true,
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
      dispose: vi.fn(),
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

const FULL = { particleScale: 1 };
const LITE = { particleScale: 0.5 };

const SIX_REGIONS = [
  "North America",
  "South America",
  "Europe",
  "Africa",
  "Middle East",
  "Asia Pacific",
];

function taggedHubIndices(group: THREE.Group): number[] {
  const out: number[] = [];
  group.traverse((c) => {
    const index = (c as THREE.Mesh).userData?.hubIndex;
    if (typeof index === "number") out.push(index);
  });
  return out;
}

function byCategoryId(group: THREE.Group, id: string): THREE.Object3D[] {
  const out: THREE.Object3D[] = [];
  group.traverse((c) => {
    if ((c as THREE.Mesh).userData?.categoryId === id) out.push(c);
  });
  return out;
}

describe("atlas eight-category coverage (CS-GAT-008)", () => {
  // jsdom logs a virtual-console error for every real getContext call even
  // though the builders catch it; stub it so suite exit codes stay honest.
  beforeEach(() => {
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("registers all six geographic regions", () => {
    const regions = ATLAS_CATEGORIES.filter((c) => c.kind === "region");
    expect(regions.map((c) => c.name).sort()).toEqual([...SIX_REGIONS].sort());
  });

  it("anchors every region to a valid hub position", () => {
    for (const name of SIX_REGIONS) {
      const hub = REGION_HUBS.find((h) => h.name === name);
      expect(hub, `hub for ${name}`).toBeDefined();
      expect(isValidGeo(hub!.lat, hub!.lon)).toBe(true);
    }
  });

  it("registers the Global Oceans overlay and renders it at every quality", () => {
    const oceans = ATLAS_CATEGORIES.find((c) => c.kind === "ocean");
    expect(oceans?.name).toBe("Global Oceans");
    expect(isValidGeo(OCEAN_MARKER.lat, OCEAN_MARKER.lon)).toBe(true);
    for (const quality of [FULL, LITE]) {
      const earth = buildEarth(quality);
      const marks = byCategoryId(earth.group, "global-oceans");
      expect(marks.length).toBeGreaterThan(0);
      expect(
        marks.some((m) => m instanceof THREE.Sprite),
        "ocean label sprite"
      ).toBe(true);
      earth.dispose();
    }
  });

  it("registers cross-border corridors and renders arcs on the globe", () => {
    const corridors = ATLAS_CATEGORIES.find((c) => c.kind === "corridor");
    expect(corridors?.name).toBe("Cross-Border Corridors");
    expect(CORRIDOR_ROUTES.length).toBeGreaterThanOrEqual(4);
    const group = buildCorridorGroup(REGION_HUBS, EARTH_RADIUS * 1.01);
    expect(group.children.length).toBe(CORRIDOR_ROUTES.length);
    for (const arc of group.children) {
      expect(arc.userData.categoryId).toBe("cross-border-corridors");
      expect(typeof arc.userData.from).toBe("string");
      expect(typeof arc.userData.to).toBe("string");
    }
    const earth = buildEarth(FULL);
    expect(
      byCategoryId(earth.group, "cross-border-corridors").length
    ).toBeGreaterThan(0);
    earth.dispose();
  });

  it("holds exactly eight categories with unique ids", () => {
    expect(ATLAS_CATEGORIES).toHaveLength(8);
    const ids = ATLAS_CATEGORIES.map((c) => c.id);
    expect(new Set(ids).size).toBe(8);
  });

  it("exposes all eight categories as accessible text", () => {
    render(<GlobeControls controller={new GlobeController()} />);
    const list = screen.getByTestId("atlas-categories");
    for (const category of ATLAS_CATEGORIES) {
      expect(list.textContent).toContain(category.name);
    }
    expect(list.textContent).toContain("Illustrative");
  });

  it("renders every region hub at reduced quality (no 4-hub truncation)", () => {
    const earth = buildEarth(LITE);
    const distinct = new Set(taggedHubIndices(earth.group));
    expect(distinct.size).toBe(REGION_HUBS.length);
    expect(distinct.has(REGION_HUBS.findIndex((h) => h.name === "Middle East"))).toBe(
      true
    );
    expect(
      distinct.has(REGION_HUBS.findIndex((h) => h.name === "Asia Pacific"))
    ).toBe(true);
    earth.dispose();
  });

  it("skips invalid corridor endpoints without throwing", () => {
    const corrupt = [
      ...REGION_HUBS,
      { name: "Nowhere", lat: Number.NaN, lon: 0, gold: false },
    ];
    const routes: [string, string][] = [...CORRIDOR_ROUTES, ["Nowhere", "Europe"]];
    let group: THREE.Group | undefined;
    expect(() => {
      group = buildCorridorGroup(corrupt, EARTH_RADIUS, routes);
    }).not.toThrow();
    expect(group!.children.length).toBe(CORRIDOR_ROUTES.length);
    expect(isValidGeo(Number.NaN, 0)).toBe(false);
    expect(isValidGeo(0, 200)).toBe(false);
    expect(isValidGeo(100, 0)).toBe(false);
  });

  it("builds every category label without runtime exceptions", () => {
    for (const category of ATLAS_CATEGORIES) {
      let label: THREE.Sprite | undefined;
      expect(() => {
        label = makeLabelSprite(category.name);
      }).not.toThrow();
      expect(label!.scale.y).toBeCloseTo(0.18, 5);
    }
  });

  it("keeps drag rotation, zoom, and reset working", () => {
    const controller = new GlobeController();
    controller.addRotation(100, 40);
    expect(controller.getState().yaw).not.toBe(0);
    controller.zoomBy(-1);
    expect(controller.getState().zoom).toBeLessThan(0);
    controller.select(2);
    controller.reset();
    expect(controller.getState()).toEqual({
      yaw: 0,
      pitch: 0,
      zoom: 0,
      selected: -1,
    });
  });

  it("renders a static frame under reduced motion without crashing", () => {
    // WebGL is mocked available above, so this exercises the real
    // reduced-motion branch (one static frame) with real builders.
    const { container } = render(
      <GlobalHeroScene
        motion="reduced"
        paused={false}
        controller={new GlobeController()}
      />
    );
    expect(container.querySelector("canvas")).not.toBeNull();
    expect(screen.queryByTestId("webgl-fallback")).toBeNull();
  });

  it("marks corridors illustrative and claims no live monitoring", () => {
    const corridors = ATLAS_CATEGORIES.find((c) => c.kind === "corridor")!;
    expect(corridors.blurb).toMatch(/illustrative/i);
    expect(corridors.blurb).toMatch(/synthetic/i);
    const banned = ["real-time", "realtime", "live data", "live feed"];
    for (const category of ATLAS_CATEGORIES) {
      const text = `${category.name} ${category.blurb}`.toLowerCase();
      for (const phrase of banned) {
        expect(text).not.toContain(phrase);
      }
    }
  });
});

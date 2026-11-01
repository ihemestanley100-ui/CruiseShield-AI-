import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { buildBrain } from "./brain";
import { buildEarth, EARTH_RADIUS, REGION_HUBS } from "./earth";
import { buildNetwork } from "./network";
import { buildOrbital } from "./orbital";
import { latLongToVec3, makeLabelSprite } from "./shared";
import { buildStars } from "./stars";
import { isPageVisible, isWebGLAvailable } from "./webgl";

const FULL = { particleScale: 1 };
const LITE = { particleScale: 0.5 };

describe("landing scene builders", () => {
  it("builds an earth with globe, atmosphere, hubs, and rings", () => {
    const earth = buildEarth(FULL);
    expect(earth.group.children.length).toBeGreaterThan(10);
    expect(REGION_HUBS).toHaveLength(8);
    earth.update(0.016, 1);
    expect(() => earth.dispose()).not.toThrow();
  });

  it("keeps region label sprites small relative to the globe (R-04)", () => {
    const label = makeLabelSprite("South America");
    // Label height must stay well under 10% of the globe diameter.
    expect(label.scale.y).toBeLessThan(EARTH_RADIUS * 2 * 0.1);
    expect(label.scale.y).toBeCloseTo(0.18, 5);
    // Aspect preserved: width scales with the same base unit.
    expect(label.scale.x / label.scale.y).toBeGreaterThan(1);
  });

  it("builds a neural brain with nodes, edges, core, and pulses", () => {
    const brain = buildBrain(FULL);
    // nodes + edges + core + halo + light + pulses + 2 hemisphere glows
    expect(brain.group.children.length).toBe(8);
    brain.update(0.016, 1);
    brain.update(0.016, 2);
    expect(() => brain.dispose()).not.toThrow();
  });

  it("builds brain-to-earth beams with travelling pulses", () => {
    const hubs = REGION_HUBS.map((hub) =>
      latLongToVec3(hub.lat, hub.lon, EARTH_RADIUS)
    );
    const network = buildNetwork(new THREE.Vector3(0, 1, 0), hubs, FULL);
    expect(network.group.children.length).toBeGreaterThan(hubs.length);
    network.update(0.016, 1);
    expect(() => network.dispose()).not.toThrow();
  });

  it("builds an orbital layer with paths and satellites", () => {
    const orbital = buildOrbital(FULL);
    expect(orbital.group.children.length).toBe(3 + 6);
    orbital.update(0.016, 1);
    expect(() => orbital.dispose()).not.toThrow();
  });

  it("builds a starfield backdrop", () => {
    const stars = buildStars(FULL);
    expect(stars.group.children.length).toBe(4);
    stars.update(0.016, 1);
    expect(() => stars.dispose()).not.toThrow();
  });

  it("scales particle density down for mobile quality", () => {
    const full = buildBrain(FULL);
    const lite = buildBrain(LITE);
    const fullCount = (
      full.group.children[0] as THREE.Points
    ).geometry.getAttribute("position").count;
    const liteCount = (
      lite.group.children[0] as THREE.Points
    ).geometry.getAttribute("position").count;
    expect(liteCount).toBeLessThan(fullCount);
    full.dispose();
    lite.dispose();
  });

  it("maps lat/long onto the sphere surface", () => {
    const point = latLongToVec3(0, 0, EARTH_RADIUS);
    expect(point.length()).toBeCloseTo(EARTH_RADIUS, 5);
    const north = latLongToVec3(90, 0, 1);
    expect(north.y).toBeCloseTo(1, 5);
  });

  it("reports WebGL unavailable in jsdom", () => {
    expect(isWebGLAvailable()).toBe(false);
  });

  it("treats a visible prerender page as visible", () => {
    expect(document.visibilityState).not.toBe("hidden");
    expect(isPageVisible()).toBe(true);
  });

  it("rotates globe and brain independently within specified periods", () => {
    const earth = buildEarth(FULL);
    const globe = earth.group.children[0] as THREE.Mesh;
    earth.update(1, 0);
    // 0.05 rad/s -> ~125.7 s/rev (spec 90-150 s).
    expect(globe.rotation.y).toBeCloseTo(0.05, 5);
    const brain = buildBrain(FULL);
    brain.update(1, 0);
    // 0.09 rad/s -> ~69.8 s/rev (spec 45-75 s).
    expect(brain.group.rotation.y).toBeCloseTo(0.09, 5);
    earth.dispose();
    brain.dispose();
  });

  it("cycles hemisphere illumination in antiphase", () => {
    const brain = buildBrain(FULL);
    const sprites = brain.group.children.filter(
      (c): c is THREE.Sprite => c instanceof THREE.Sprite
    );
    // coreHalo + hemiL + hemiR.
    expect(sprites).toHaveLength(3);
    const left = sprites[1].material as THREE.SpriteMaterial;
    const right = sprites[2].material as THREE.SpriteMaterial;
    brain.update(0.016, 0);
    expect(left.opacity + right.opacity).toBeCloseTo(0.44, 5);
    const leftAt0 = left.opacity;
    brain.update(0.016, 2.6);
    expect(left.opacity).not.toBeCloseTo(leftAt0, 2);
    expect(left.opacity + right.opacity).toBeCloseTo(0.44, 5);
    brain.dispose();
  });

  it("illuminates region hubs sequentially, not uniformly", () => {
    const earth = buildEarth(FULL);
    earth.update(0.016, 0);
    const halos = earth.group.children.filter(
      (c): c is THREE.Sprite =>
        c instanceof THREE.Sprite &&
        (c.material as THREE.SpriteMaterial).opacity < 1
    );
    expect(halos).toHaveLength(REGION_HUBS.length);
    const values = halos.map(
      (h) => (h.material as THREE.SpriteMaterial).opacity
    );
    expect(Math.max(...values) - Math.min(...values)).toBeGreaterThan(0.1);
    earth.dispose();
  });

  it("flashes hub rings in sync with beam pulses", () => {
    const hubs = REGION_HUBS.map((hub) =>
      latLongToVec3(hub.lat, hub.lon, EARTH_RADIUS)
    );
    const network = buildNetwork(new THREE.Vector3(0, 1, 0), hubs, FULL);
    const rings = network.group.children.filter(
      (c): c is THREE.Mesh =>
        c instanceof THREE.Mesh && c.geometry.type === "RingGeometry"
    );
    expect(rings.length).toBe(hubs.length);
    network.update(0.016, 0);
    const at0 = rings.map(
      (r) => (r.material as THREE.MeshBasicMaterial).opacity
    );
    network.update(0.016, 1.8);
    const at18 = rings.map(
      (r) => (r.material as THREE.MeshBasicMaterial).opacity
    );
    expect(at0[0]).not.toBeCloseTo(at18[0], 2);
    for (const v of [...at0, ...at18]) {
      expect(v).toBeGreaterThanOrEqual(0.55);
      expect(v).toBeLessThanOrEqual(1);
    }
    network.dispose();
  });
});

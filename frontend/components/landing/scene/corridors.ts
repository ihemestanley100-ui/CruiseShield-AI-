/* Cross-border corridor arcs: illustrative paths between region hubs.
 * Same tube-on-curve technique as the brain-to-earth beams; unresolvable
 * or invalid endpoints are skipped so bad data fails safe (no throw). */

import * as THREE from "three";
import { CORRIDOR_ROUTES, isValidGeo } from "./categories";
import {
  COLORS,
  latLongToVec3,
  type SceneQuality,
} from "./shared";
import type { RegionHub } from "./earth";

export function buildCorridorGroup(
  hubs: RegionHub[],
  radius: number,
  routes: [string, string][] = CORRIDOR_ROUTES,
  quality: SceneQuality = { particleScale: 1 }
): THREE.Group {
  const group = new THREE.Group();
  group.userData.categoryId = "cross-border-corridors";
  const material = new THREE.MeshBasicMaterial({
    color: COLORS.cyan,
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const segments = quality.particleScale >= 1 ? 40 : 24;
  for (const [from, to] of routes) {
    const a = hubs.find((h) => h.name === from);
    const b = hubs.find((h) => h.name === to);
    if (!a || !b) continue;
    if (!isValidGeo(a.lat, a.lon) || !isValidGeo(b.lat, b.lon)) continue;
    const p1 = latLongToVec3(a.lat, a.lon, radius);
    const p2 = latLongToVec3(b.lat, b.lon, radius);
    const mid = p1.clone().add(p2).multiplyScalar(0.5);
    if (mid.lengthSq() < 1e-6) continue;
    mid.normalize().multiplyScalar(radius * 1.28);
    const curve = new THREE.QuadraticBezierCurve3(p1, mid, p2);
    const arc = new THREE.Mesh(
      new THREE.TubeGeometry(curve, segments, 0.008, 6, false),
      material
    );
    arc.userData.categoryId = "cross-border-corridors";
    arc.userData.from = from;
    arc.userData.to = to;
    group.add(arc);
  }
  return group;
}

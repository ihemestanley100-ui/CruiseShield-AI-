/* Brain-to-Earth intelligence beams: curved energy paths with
 * travelling pulses plus hub rings. Decorative visualization of
 * illustrative coverage, not live surveillance. */

import * as THREE from "three";
import {
  COLORS,
  makeGlowTexture,
  type ScenePart,
  type SceneQuality,
} from "./shared";

export function buildNetwork(
  brainAnchor: THREE.Vector3,
  hubs: THREE.Vector3[],
  quality: SceneQuality
): ScenePart {
  const group = new THREE.Group();
  const glow = makeGlowTexture();
  const curves: THREE.QuadraticBezierCurve3[] = [];
  const rings: THREE.Mesh[] = [];
  const tubeMaterial = new THREE.MeshBasicMaterial({
    color: COLORS.cyan,
    transparent: true,
    opacity: 0.42,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  hubs.forEach((hub, index) => {
    const mid = brainAnchor
      .clone()
      .lerp(hub, 0.5)
      .add(new THREE.Vector3(0, 0.35, 0));
    // Alternate slight lateral bow so beams separate visually.
    mid.x += (index % 2 === 0 ? 1 : -1) * 0.22;
    const curve = new THREE.QuadraticBezierCurve3(
      brainAnchor.clone(), mid, hub.clone()
    );
    curves.push(curve);
    group.add(new THREE.Mesh(
      new THREE.TubeGeometry(curve, 40, 0.012, 6, false),
      tubeMaterial
    ));
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.06, 0.085, 32),
      new THREE.MeshBasicMaterial({
        color: COLORS.gold,
        transparent: true,
        opacity: 0.8,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    rings.push(ring);
    ring.position.copy(hub);
    ring.lookAt(hub.clone().multiplyScalar(2));
    group.add(ring);
  });

  // Travelling pulses: several per beam.
  const perBeam = quality.particleScale >= 1 ? 3 : 2;
  const total = curves.length * perBeam;
  const pulseGeometry = new THREE.BufferGeometry();
  const pulsePositions = new Float32Array(total * 3);
  pulseGeometry.setAttribute("position", new THREE.BufferAttribute(pulsePositions, 3));
  group.add(new THREE.Points(
    pulseGeometry,
    new THREE.PointsMaterial({
      size: 0.075,
      map: glow,
      color: COLORS.iceBlue,
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  ));
  const point = new THREE.Vector3();

  return {
    group,
    update: (_dt, t) => {
      const attr = pulseGeometry.getAttribute("position") as THREE.BufferAttribute;
      let k = 0;
      curves.forEach((curve, c) => {
        for (let p = 0; p < perBeam; p++) {
          const f = (t * 0.14 + p / perBeam + c * 0.13) % 1;
          curve.getPoint(f, point);
          attr.setXYZ(k++, point.x, point.y, point.z);
        }
      });
      attr.needsUpdate = true;
      // Hub rings flash as each beam's lead pulse arrives: same phase
      // family as f above, peaking near arrival (phase ~0.95).
      rings.forEach((ring, c) => {
        const material = ring.material as THREE.MeshBasicMaterial;
        const arrival = Math.pow(
          Math.max(0, Math.sin(2 * Math.PI * (t * 0.14 + c * 0.13 + 0.3))), 6);
        material.opacity = 0.55 + 0.45 * arrival;
      });
    },
    dispose: () => {
      group.traverse((child) => {
        const mesh = child as THREE.Mesh;
        mesh.geometry?.dispose();
      });
      tubeMaterial.dispose();
      const points = group.children.find(
        (c): c is THREE.Points => c instanceof THREE.Points
      );
      (points?.material as THREE.Material | undefined)?.dispose();
      glow.dispose();
    },
  };
}

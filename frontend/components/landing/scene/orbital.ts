/* Orbital layer: tilted orbit paths, stylized satellites, comm
 * nodes, and signal pulses. Illustrative objects, not owned assets. */

import * as THREE from "three";
import {
  COLORS,
  makeGlowTexture,
  type ScenePart,
  type SceneQuality,
} from "./shared";

const ORBITS = [
  { radius: 3.4, tiltX: 1.25, tiltY: 0.2, speed: 0.1 },
  { radius: 3.9, tiltX: 1.05, tiltY: -0.5, speed: -0.07 },
  { radius: 4.4, tiltX: 1.45, tiltY: 0.9, speed: 0.05 },
];

function buildSatellite(glow: THREE.Texture): THREE.Group {
  const satellite = new THREE.Group();
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0x9fb6cc,
    roughness: 0.35,
    metalness: 0.85,
  });
  satellite.add(new THREE.Mesh(
    new THREE.BoxGeometry(0.1, 0.1, 0.16), bodyMaterial
  ));
  const panelMaterial = new THREE.MeshStandardMaterial({
    color: COLORS.electricBlue,
    roughness: 0.5,
    metalness: 0.6,
    emissive: COLORS.electricBlue,
    emissiveIntensity: 0.35,
  });
  for (const side of [-1, 1]) {
    const panel = new THREE.Mesh(
      new THREE.BoxGeometry(0.22, 0.02, 0.12), panelMaterial
    );
    panel.position.x = side * 0.17;
    satellite.add(panel);
  }
  const beacon = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glow,
    color: COLORS.gold,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
  }));
  beacon.scale.set(0.16, 0.16, 1);
  beacon.position.y = 0.1;
  satellite.add(beacon);
  satellite.userData.beacon = beacon;
  return satellite;
}

export function buildOrbital(quality: SceneQuality): ScenePart {
  const group = new THREE.Group();
  const glow = makeGlowTexture();
  const satellites: { node: THREE.Group; orbit: number; angle: number }[] = [];

  ORBITS.forEach((orbit, index) => {
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= 180; i++) {
      const a = (i / 180) * Math.PI * 2;
      points.push(new THREE.Vector3(
        Math.cos(a) * orbit.radius, 0, Math.sin(a) * orbit.radius
      ));
    }
    const path = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({
        color: COLORS.cyan,
        transparent: true,
        opacity: 0.22,
      })
    );
    path.rotation.x = orbit.tiltX;
    path.rotation.y = orbit.tiltY;
    group.add(path);

    const perOrbit = quality.particleScale >= 1 ? 2 : 1;
    for (let s = 0; s < perOrbit; s++) {
      const satellite = buildSatellite(glow);
      satellites.push({
        node: satellite,
        orbit: index,
        angle: ((s / perOrbit) + index * 0.37) * Math.PI * 2,
      });
      group.add(satellite);
    }
  });

  const tiltGroups = group.children.filter(
    (c): c is THREE.Line => c instanceof THREE.Line
  );

  return {
    group,
    update: (dt, t) => {
      satellites.forEach(({ node, orbit, angle }) => {
        const config = ORBITS[orbit];
        const a = angle + t * config.speed;
        const local = new THREE.Vector3(
          Math.cos(a) * config.radius, 0, Math.sin(a) * config.radius
        );
        // Match the tilted path orientation.
        local.applyEuler(new THREE.Euler(config.tiltX, config.tiltY, 0, "YXZ"));
        node.position.copy(local);
        node.rotation.y = -a;
        const beacon = node.userData.beacon as THREE.Sprite;
        const blink = 0.6 + Math.abs(Math.sin(t * 2 + angle)) * 0.5;
        beacon.scale.set(0.16 * blink, 0.16 * blink, 1);
      });
      tiltGroups.forEach((line, i) => {
        line.rotation.z += dt * 0.01 * (i % 2 === 0 ? 1 : -1);
      });
    },
    dispose: () => {
      group.traverse((child) => {
        const mesh = child as THREE.Mesh;
        mesh.geometry?.dispose();
        const material = mesh.material as THREE.Material | undefined;
        material?.dispose();
      });
      glow.dispose();
    },
  };
}

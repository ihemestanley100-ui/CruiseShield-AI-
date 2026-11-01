/* Deep-space backdrop: layered starfield + faint teal nebulae. */

import * as THREE from "three";
import {
  COLORS,
  makeGlowTexture,
  type ScenePart,
  type SceneQuality,
} from "./shared";

export function buildStars(quality: SceneQuality): ScenePart {
  const group = new THREE.Group();
  const count = Math.round(1400 * quality.particleScale);
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const white = new THREE.Color(COLORS.white);
  const ice = new THREE.Color(COLORS.iceBlue);
  const dim = new THREE.Color(0x5b7a99);
  const scratch = new THREE.Color();
  let seed = 99;
  const rand = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  for (let i = 0; i < count; i++) {
    const radius = 26 + rand() * 40;
    const theta = rand() * Math.PI * 2;
    const phi = Math.acos(rand() * 2 - 1);
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    const pick = rand();
    if (pick < 0.2) scratch.copy(white);
    else if (pick < 0.5) scratch.copy(ice);
    else scratch.copy(dim);
    const brightness = 0.35 + rand() * 0.65;
    colors[i * 3] = scratch.r * brightness;
    colors[i * 3 + 1] = scratch.g * brightness;
    colors[i * 3 + 2] = scratch.b * brightness;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const glow = makeGlowTexture();
  group.add(new THREE.Points(
    geometry,
    new THREE.PointsMaterial({
      size: 0.55,
      map: glow,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      sizeAttenuation: true,
    })
  ));

  // Faint nebula washes (teal/blue only).
  const nebulaTexture = makeGlowTexture(
    "rgba(0, 217, 255, 0.16)", "rgba(0, 217, 255, 0)"
  );
  for (const [x, y, z, size] of [
    [-18, 8, -30, 26],
    [20, -6, -34, 30],
    [2, 14, -40, 34],
  ] as const) {
    const nebula = new THREE.Sprite(new THREE.SpriteMaterial({
      map: nebulaTexture,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    }));
    nebula.position.set(x, y, z);
    nebula.scale.set(size, size, 1);
    group.add(nebula);
  }

  return {
    group,
    update: (dt) => {
      group.rotation.y += dt * 0.0025;
    },
    dispose: () => {
      group.traverse((child) => {
        const mesh = child as THREE.Mesh;
        mesh.geometry?.dispose();
        const material = mesh.material as THREE.Material | undefined;
        material?.dispose();
      });
      glow.dispose();
      nebulaTexture.dispose();
    },
  };
}

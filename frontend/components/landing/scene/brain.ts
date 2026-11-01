/* Procedural neural brain: two-hemisphere node field, synaptic
 * connections, illuminated core, and gold pulses travelling the
 * network. Recognizable brain silhouette through volume shaping. */

import * as THREE from "three";
import {
  COLORS,
  makeGlowTexture,
  type ScenePart,
  type SceneQuality,
} from "./shared";

const NODE_COUNT = 650;
const MAX_EDGES = 1500;
const PULSE_COUNT = 70;

function mulberry(seed: number): () => number {
  let s = seed;
  return () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function buildBrain(quality: SceneQuality): ScenePart {
  const group = new THREE.Group();
  const rand = mulberry(20261031);
  const count = Math.round(NODE_COUNT * quality.particleScale);

  // Sample a flattened, two-lobed volume with a center fissure.
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const gold = new THREE.Color(COLORS.gold);
  const cyan = new THREE.Color(COLORS.cyan);
  const blue = new THREE.Color(COLORS.electricBlue);
  const scratch = new THREE.Color();
  let placed = 0;
  let guard = 0;
  while (placed < count && guard < count * 40) {
    guard++;
    const x = (rand() * 2 - 1) * 1.2;
    const y = (rand() * 2 - 1) * 0.82;
    const z = (rand() * 2 - 1) * 0.88;
    // Fissure between hemispheres + slightly flattened base.
    if (Math.abs(x) < 0.09) continue;
    const r = (x / 1.2) ** 2 + (y / 0.82) ** 2 + (z / 0.88) ** 2;
    if (r > 1 || r < 0.08) continue;
    // Cortical folds: modulate radius with low-frequency waves.
    const fold = 1 + 0.07 * Math.sin(x * 9 + y * 5) * Math.sin(z * 8);
    positions[placed * 3] = x * fold;
    positions[placed * 3 + 1] = y * fold;
    positions[placed * 3 + 2] = z * fold;
    const pick = rand();
    if (pick < 0.1) scratch.copy(gold);
    else if (pick < 0.45) scratch.copy(cyan);
    else scratch.copy(blue).lerp(cyan, rand() * 0.5);
    colors[placed * 3] = scratch.r;
    colors[placed * 3 + 1] = scratch.g;
    colors[placed * 3 + 2] = scratch.b;
    placed++;
  }
  const nodeGeometry = new THREE.BufferGeometry();
  nodeGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  nodeGeometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const glow = makeGlowTexture();
  const nodes = new THREE.Points(
    nodeGeometry,
    new THREE.PointsMaterial({
      size: 0.045,
      map: glow,
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    })
  );
  group.add(nodes);

  // Synaptic edges between near neighbors.
  const edgePositions: number[] = [];
  const edgePairs: [number, number][] = [];
  for (let i = 0; i < count && edgePairs.length < MAX_EDGES; i++) {
    let linked = 0;
    for (let j = i + 1; j < count && linked < 2; j++) {
      const dx = positions[i * 3] - positions[j * 3];
      const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
      const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
      if (dx * dx + dy * dy + dz * dz < 0.09) {
        edgePairs.push([i, j]);
        edgePositions.push(
          positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
          positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]
        );
        linked++;
      }
    }
  }
  const edgeGeometry = new THREE.BufferGeometry();
  edgeGeometry.setAttribute(
    "position", new THREE.Float32BufferAttribute(edgePositions, 3)
  );
  group.add(new THREE.LineSegments(
    edgeGeometry,
    new THREE.LineBasicMaterial({
      color: COLORS.electricBlue,
      transparent: true,
      opacity: 0.34,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  ));

  // Illuminated central core.
  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.2, 1),
    new THREE.MeshBasicMaterial({ color: COLORS.iceBlue })
  );
  group.add(core);
  const coreHalo = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glow,
    color: COLORS.cyan,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
  }));
  coreHalo.scale.set(1.1, 1.1, 1);
  group.add(coreHalo);
  const coreLight = new THREE.PointLight(COLORS.cyan, 18, 14, 2);
  group.add(coreLight);

  // Hemisphere illumination cycle: two soft glows breathing in antiphase.
  const hemiL = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glow,
    color: COLORS.cyan,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
  }));
  hemiL.scale.set(1.5, 1.1, 1);
  hemiL.position.set(-0.62, 0, 0);
  group.add(hemiL);
  const hemiR = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glow,
    color: COLORS.gold,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
  }));
  hemiR.scale.set(1.5, 1.1, 1);
  hemiR.position.set(0.62, 0, 0);
  group.add(hemiR);

  // Gold pulses travelling random edges.
  const pulses = Math.round(PULSE_COUNT * quality.particleScale);
  const pulseGeometry = new THREE.BufferGeometry();
  const pulsePositions = new Float32Array(pulses * 3);
  pulseGeometry.setAttribute("position", new THREE.BufferAttribute(pulsePositions, 3));
  const pulsePoints = new THREE.Points(
    pulseGeometry,
    new THREE.PointsMaterial({
      size: 0.06,
      map: glow,
      color: COLORS.gold,
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  group.add(pulsePoints);
  const assignments = Array.from({ length: pulses }, (_, k) => ({
    edge: edgePairs.length > 0 ? edgePairs[k % edgePairs.length] : [0, 0],
    offset: rand(),
    speed: 0.25 + rand() * 0.5,
  }));

  const baseY = group.position.y;
  return {
    group,
    update: (dt, t) => {
      // ~69.8 s per revolution (spec: 45-75 s), independent of the globe.
      group.rotation.y += dt * 0.09;
      group.position.y = baseY + Math.sin(t * 0.5) * 0.07;
      core.rotation.y -= dt * 0.4;
      // Hemisphere illumination: slow antiphase breathing (~10.5 s cycle).
      const hemiPhase = Math.sin(t * 0.6);
      (hemiL.material as THREE.SpriteMaterial).opacity = 0.22 + 0.14 * hemiPhase;
      (hemiR.material as THREE.SpriteMaterial).opacity = 0.22 - 0.14 * hemiPhase;
      const pulse = 0.75 + Math.sin(t * 2.1) * 0.2;
      coreHalo.scale.set(1.1 * pulse + 0.25, 1.1 * pulse + 0.25, 1);
      const attr = pulseGeometry.getAttribute("position") as THREE.BufferAttribute;
      assignments.forEach(({ edge, offset, speed }, k) => {
        const f = (offset + t * speed * 0.35) % 1;
        const [a, b] = edge;
        attr.setXYZ(
          k,
          positions[a * 3] + (positions[b * 3] - positions[a * 3]) * f,
          positions[a * 3 + 1] + (positions[b * 3 + 1] - positions[a * 3 + 1]) * f,
          positions[a * 3 + 2] + (positions[b * 3 + 2] - positions[a * 3 + 2]) * f
        );
      });
      attr.needsUpdate = true;
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

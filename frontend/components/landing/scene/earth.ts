/* Procedural digital Earth: stylized continents, night-side city
 * lights, graticule, atmosphere shell, regional hubs + labels, and
 * orbital guide rings. All textures are canvas-drawn; no map services. */

import * as THREE from "three";
import {
  COLORS,
  canvas2d,
  latLongToVec3,
  makeGlowTexture,
  makeLabelSprite,
  type ScenePart,
  type SceneQuality,
} from "./shared";

export const EARTH_RADIUS = 1.6;

/* Stylized continent blobs on an equirectangular canvas (x: 0..1 maps
 * lon -180..180, y: 0..1 maps lat 90..-90). Cinematic impression, not
 * cartography. */
const CONTINENTS: [number, number, number, number][] = [
  // North America (+ Greenland, Central America taper)
  [0.16, 0.2, 0.11, 0.1],
  [0.3, 0.12, 0.05, 0.05],
  [0.2, 0.36, 0.05, 0.06],
  // South America
  [0.27, 0.55, 0.06, 0.14],
  // Europe + Africa
  [0.52, 0.2, 0.06, 0.07],
  [0.52, 0.4, 0.07, 0.16],
  // Middle East / Asia
  [0.62, 0.26, 0.13, 0.12],
  [0.78, 0.2, 0.09, 0.09],
  // SE Asia + Oceania
  [0.76, 0.44, 0.05, 0.07],
  [0.86, 0.62, 0.06, 0.07],
];

export interface RegionHub {
  name: string;
  lat: number;
  lon: number;
  gold: boolean;
}

export const REGION_HUBS: RegionHub[] = [
  { name: "North America", lat: 40, lon: -100, gold: false },
  { name: "South America", lat: -15, lon: -60, gold: false },
  { name: "Europe", lat: 50, lon: 10, gold: true },
  { name: "Africa", lat: 5, lon: 20, gold: false },
  { name: "Middle East", lat: 25, lon: 45, gold: true },
  { name: "Asia", lat: 35, lon: 100, gold: false },
  { name: "Asia Pacific", lat: 15, lon: 120, gold: true },
  { name: "Oceania", lat: -25, lon: 135, gold: false },
];

function hex(value: number): string {
  return `#${value.toString(16).padStart(6, "0")}`;
}

function drawSurface(): HTMLCanvasElement {
  const w = 1024;
  const h = 512;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas2d(canvas);
  if (!ctx) return canvas;
  const ocean = ctx.createLinearGradient(0, 0, 0, h);
  ocean.addColorStop(0, hex(COLORS.oceanDeep));
  ocean.addColorStop(0.5, hex(COLORS.ocean));
  ocean.addColorStop(1, hex(COLORS.oceanDeep));
  ctx.fillStyle = ocean;
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = hex(COLORS.land);
  for (const [cx, cy, rx, ry] of CONTINENTS) {
    ctx.beginPath();
    ctx.ellipse(cx * w, cy * h, rx * w, ry * h, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  // Graticule every 20 degrees.
  ctx.strokeStyle = "rgba(30, 77, 123, 0.8)";
  ctx.lineWidth = 1;
  for (let lon = 0; lon < 360; lon += 20) {
    const x = ((lon / 360) * w + w / 2) % w;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let lat = -80; lat <= 80; lat += 20) {
    const y = ((90 - lat) / 180) * h;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }
  return canvas;
}

function drawCityLights(seed: number): HTMLCanvasElement {
  const w = 512;
  const h = 256;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas2d(canvas);
  if (!ctx) return canvas;
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, w, h);
  let s = seed;
  const rand = () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
  ctx.fillStyle = hex(COLORS.cityLight);
  for (const [cx, cy, rx, ry] of CONTINENTS) {
    const count = Math.floor(rx * ry * 2600);
    for (let i = 0; i < count; i++) {
      const angle = rand() * Math.PI * 2;
      const dist = Math.sqrt(rand());
      const x = (cx + Math.cos(angle) * rx * dist * 0.9) * w;
      const y = (cy + Math.sin(angle) * ry * dist * 0.9) * h;
      const size = rand() < 0.12 ? 2 : 1;
      ctx.globalAlpha = 0.35 + rand() * 0.65;
      ctx.fillRect(x, y, size, size);
    }
  }
  ctx.globalAlpha = 1;
  return canvas;
}

export function buildEarth(quality: SceneQuality): ScenePart {
  const group = new THREE.Group();
  const map = new THREE.CanvasTexture(drawSurface());
  map.colorSpace = THREE.SRGBColorSpace;
  const emissiveMap = new THREE.CanvasTexture(drawCityLights(84721));
  emissiveMap.colorSpace = THREE.SRGBColorSpace;
  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(EARTH_RADIUS, 64, 40),
    new THREE.MeshStandardMaterial({
      map,
      emissiveMap,
      emissive: new THREE.Color(COLORS.cityLight),
      emissiveIntensity: 1.1,
      roughness: 0.85,
      metalness: 0.15,
    })
  );
  group.add(globe);

  // Atmosphere: fresnel-glow shell.
  const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(EARTH_RADIUS * 1.06, 48, 32),
    new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(COLORS.cyan) },
      },
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 glowColor;
        varying vec3 vNormal;
        void main() {
          float rim = pow(1.0 - abs(vNormal.z), 2.4);
          gl_FragColor = vec4(glowColor, rim * 0.85);
        }
      `,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    })
  );
  group.add(atmosphere);

  // Guide rings hugging the surface (equator + two latitudes).
  const guideMaterial = new THREE.LineBasicMaterial({
    color: COLORS.cyan,
    transparent: true,
    opacity: 0.28,
  });
  for (const lat of [-30, 0, 30]) {
    const radius = EARTH_RADIUS * 1.004 * Math.cos((lat * Math.PI) / 180);
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= 128; i++) {
      const a = (i / 128) * Math.PI * 2;
      points.push(new THREE.Vector3(
        Math.cos(a) * radius,
        EARTH_RADIUS * 1.004 * Math.sin((lat * Math.PI) / 180),
        Math.sin(a) * radius
      ));
    }
    group.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      guideMaterial
    ));
  }

  // Regional hubs: glowing markers + labels.
  const glow = makeGlowTexture();
  const hubHalos: THREE.Sprite[] = [];
  const hubCount = Math.max(
    4, Math.round(REGION_HUBS.length * quality.particleScale)
  );
  REGION_HUBS.slice(0, hubCount).forEach((hub) => {
    const pos = latLongToVec3(hub.lat, hub.lon, EARTH_RADIUS * 1.01);
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.028, 12, 12),
      new THREE.MeshBasicMaterial({
        color: hub.gold ? COLORS.gold : COLORS.cyan,
      })
    );
    marker.position.copy(pos);
    group.add(marker);
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({
      map: glow,
      color: hub.gold ? COLORS.gold : COLORS.cyan,
      transparent: true,
      opacity: 0.7,
      depthWrite: false,
    }));
    halo.scale.set(0.22, 0.22, 1);
    halo.position.copy(pos);
    group.add(halo);
    hubHalos.push(halo);
    const label = makeLabelSprite(hub.name, hub.gold ? "#ffc66d" : "#8beaff");
    label.position.copy(pos.clone().multiplyScalar(1.22));
    group.add(label);
  });

  // Tilted orbital guide rings.
  const ringMaterial = new THREE.MeshBasicMaterial({
    color: COLORS.electricBlue,
    transparent: true,
    opacity: 0.4,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const ring1 = new THREE.Mesh(
    new THREE.TorusGeometry(EARTH_RADIUS * 1.45, 0.006, 8, 160),
    ringMaterial
  );
  ring1.rotation.x = Math.PI / 2.25;
  group.add(ring1);
  const ring2 = new THREE.Mesh(
    new THREE.TorusGeometry(EARTH_RADIUS * 1.7, 0.005, 8, 160),
    ringMaterial
  );
  ring2.rotation.x = Math.PI / 1.8;
  ring2.rotation.y = 0.5;
  group.add(ring2);

  const disposables: { dispose: () => void }[] = [map, emissiveMap, glow];
  return {
    group,
    update: (dt, t) => {
      // ~125.7 s per revolution (spec: 90-150 s).
      globe.rotation.y += dt * 0.05;
      ring1.rotation.z += dt * 0.03;
      ring2.rotation.z -= dt * 0.02;
      // Sequential hub illumination: a brightness wave travelling the hubs.
      hubHalos.forEach((halo, i) => {
        const material = halo.material as THREE.SpriteMaterial;
        material.opacity = 0.55 + 0.25 * Math.sin(t * 1.4 - i * 0.9);
      });
    },
    dispose: () => {
      group.traverse((child) => {
        const mesh = child as THREE.Mesh;
        mesh.geometry?.dispose();
        const material = mesh.material as THREE.Material | undefined;
        material?.dispose();
      });
      disposables.forEach((d) => d.dispose());
    },
  };
}

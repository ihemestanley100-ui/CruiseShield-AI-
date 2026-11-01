/* Shared types + helpers for the landing hero scene (all procedural,
 * no external assets). */

import * as THREE from "three";

export interface ScenePart {
  group: THREE.Group;
  update: (dt: number, t: number) => void;
  dispose: () => void;
}

export interface SceneQuality {
  /** 1 = full particle density, 0.5 = mobile. */
  particleScale: number;
}

export const COLORS = {
  deepSpace: 0x020817,
  ocean: 0x0a2547,
  oceanDeep: 0x06152b,
  land: 0x14355e,
  graticule: 0x1e4d7b,
  cityLight: 0xffc66d,
  electricBlue: 0x087bff,
  cyan: 0x00d9ff,
  iceBlue: 0x8beaff,
  gold: 0xffc66d,
  white: 0xf7fbff,
} as const;

/** Canvas 2D context or null (jsdom throws; treat as unavailable). */
export function canvas2d(
  canvas: HTMLCanvasElement
): CanvasRenderingContext2D | null {
  try {
    return canvas.getContext("2d");
  } catch {
    return null;
  }
}

/** Soft round sprite for points/particles (avoids hard squares). */
export function makeGlowTexture(
  inner = "rgba(255,255,255,1)",
  outer = "rgba(255,255,255,0)"
): THREE.CanvasTexture {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas2d(canvas);
  if (ctx) {
    const gradient = ctx.createRadialGradient(
      size / 2, size / 2, 0, size / 2, size / 2, size / 2
    );
    gradient.addColorStop(0, inner);
    gradient.addColorStop(0.35, inner);
    gradient.addColorStop(1, outer);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/** Text sprite for in-scene labels. */
export function makeLabelSprite(
  text: string,
  color = "#8beaff",
  scale = 1
): THREE.Sprite {
  const pad = 16;
  const font = "600 26px system-ui, -apple-system, sans-serif";
  const measurer = canvas2d(document.createElement("canvas"));
  let width = 200;
  if (measurer) {
    measurer.font = font;
    width = Math.ceil(measurer.measureText(text).width) + pad * 2;
  }
  const height = 52;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas2d(canvas);
  if (ctx) {
    ctx.font = font;
    ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(2, 8, 23, 0.55)";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(0, 217, 255, 0.65)";
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, width - 2, height - 2);
    ctx.fillStyle = color;
    ctx.fillText(text, pad, height / 2 + 1);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  // R-04: label height 0.18 world units (was 0.28) — sprites rendered
  // ~25% of globe diameter; aspect preserved on both axes.
  sprite.scale.set((width / height) * 0.18 * scale, 0.18 * scale, 1);
  return sprite;
}

/** Latitude/longitude (degrees) to a point on a sphere of radius r. */
export function latLongToVec3(
  lat: number,
  lon: number,
  r: number
): THREE.Vector3 {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lon + 180) * Math.PI) / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );
}

export function disposeGroup(root: THREE.Object3D): void {
  root.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.geometry) mesh.geometry.dispose();
    const material = (mesh as THREE.Mesh).material as
      | THREE.Material
      | THREE.Material[]
      | undefined;
    if (Array.isArray(material)) {
      material.forEach((m) => disposeMaterial(m));
    } else if (material) {
      disposeMaterial(material);
    }
  });
}

function disposeMaterial(material: THREE.Material): void {
  const withMap = material as THREE.Material & {
    map?: THREE.Texture | null;
    emissiveMap?: THREE.Texture | null;
  };
  withMap.map?.dispose();
  withMap.emissiveMap?.dispose();
  material.dispose();
}

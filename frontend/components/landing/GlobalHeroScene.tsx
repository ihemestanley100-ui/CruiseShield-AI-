/* Client-only Three.js hero canvas: composition, camera, lights,
 * animation loop, resize handling, reduced-motion + pause support,
 * and full resource cleanup on unmount. Rendered via next/dynamic
 * with ssr:false so no browser API runs on the server. */

"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { buildBrain } from "./scene/brain";
import { buildEarth, EARTH_RADIUS, REGION_HUBS } from "./scene/earth";
import { buildNetwork } from "./scene/network";
import { buildOrbital } from "./scene/orbital";
import { buildStars } from "./scene/stars";
import { COLORS, latLongToVec3, type ScenePart } from "./scene/shared";
import { isPageVisible, isWebGLAvailable } from "./scene/webgl";
import { WebGLFallback } from "./WebGLFallback";

const EARTH_Y = -1.35;
const BRAIN_Y = 1.75;

interface Props {
  motion: "full" | "reduced";
  paused: boolean;
}

export function GlobalHeroScene({ motion, paused }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const motionRef = useRef(motion);
  const pausedRef = useRef(paused);
  const hiddenRef = useRef(false);
  const [failed, setFailed] = useState(false);
  motionRef.current = motion;
  pausedRef.current = paused;

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    if (!isWebGLAvailable()) {
      setFailed(true);
      return;
    }

    let renderer: THREE.WebGLRenderer | null = null;
    let frame = 0;
    let disposed = false;
    const parts: ScenePart[] = [];
    const clock = new THREE.Clock();
    const pointer = new THREE.Vector2(0, 0);
    const cameraBase = new THREE.Vector3();

    const isMobileViewport = () =>
      host.clientWidth < 768 || window.innerHeight < 560;
    const quality = {
      particleScale: isMobileViewport() ? 0.5 : 1,
    };

    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      setFailed(true);
      return;
    }
    renderer.setClearColor(COLORS.deepSpace, 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(COLORS.deepSpace, 0.012);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);

    scene.add(new THREE.AmbientLight(0x8beaff, 0.55));
    const sun = new THREE.DirectionalLight(0xf7fbff, 2.4);
    sun.position.set(6, 4, 5);
    scene.add(sun);
    const rim = new THREE.DirectionalLight(COLORS.cyan, 0.8);
    rim.position.set(-6, -2, -4);
    scene.add(rim);

    // Composition: brain floats above the globe, network links them.
    const stars = buildStars(quality);
    const earth = buildEarth(quality);
    earth.group.position.y = EARTH_Y;
    const brain = buildBrain(quality);
    brain.group.position.y = BRAIN_Y;
    const hubs = REGION_HUBS.map((hub) =>
      latLongToVec3(hub.lat, hub.lon, EARTH_RADIUS * 1.02).add(
        new THREE.Vector3(0, EARTH_Y, 0)
      )
    );
    const network = buildNetwork(
      new THREE.Vector3(0, BRAIN_Y - 0.7, 0), hubs, quality
    );
    const orbital = buildOrbital(quality);
    orbital.group.position.y = EARTH_Y;
    parts.push(stars, earth, brain, network, orbital);
    parts.forEach((part) => scene.add(part.group));

    const layout = () => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      const mobile = isMobileViewport();
      const dpr = Math.min(
        window.devicePixelRatio || 1, mobile ? 1.25 : 2
      );
      renderer?.setPixelRatio(dpr);
      renderer?.setSize(width, height, false);
      camera.aspect = width / height;
      // Pull back on narrow screens so brain + globe stay in frame.
      camera.position.set(0, mobile ? 0.7 : 0.35, mobile ? 9.6 : 7.2);
      camera.lookAt(0, 0.2, 0);
      cameraBase.copy(camera.position);
      camera.updateProjectionMatrix();
    };
    layout();
    window.addEventListener("resize", layout);

    const onPointer = (event: PointerEvent) => {
      const rect = host.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
    };
    const onVisibility = () => {
      hiddenRef.current = !isPageVisible();
    };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("pointermove", onPointer);

    const renderFrame = () => {
      if (!renderer || disposed) return;
      const allowMotion =
        !pausedRef.current && motionRef.current === "full";
      const dt = allowMotion ? Math.min(clock.getDelta(), 0.05) : 0;
      const t = clock.elapsedTime;
      if (allowMotion) {
        parts.forEach((part) => part.update(dt, t));
        // Gentle parallax, disabled under reduced motion.
        camera.position.x +=
          (cameraBase.x + pointer.x * 0.25 - camera.position.x) * 0.04;
        camera.position.y +=
          (cameraBase.y + pointer.y * 0.18 - camera.position.y) * 0.04;
        camera.lookAt(0, 0.2, 0);
      } else {
        clock.getDelta();
      }
      renderer.render(scene, camera);
    };

    // Reduced motion / paused: render one static frame (plus resizes).
    if (motionRef.current === "reduced" || pausedRef.current) {
      renderFrame();
    }
    const loop = () => {
      if (disposed) return;
      // Hidden tabs: keep the callback alive but skip all render work.
      if (!hiddenRef.current) {
        renderFrame();
      }
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", layout);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVisibility);
      parts.forEach((part) => {
        scene.remove(part.group);
        part.dispose();
      });
      renderer?.dispose();
      renderer?.domElement.remove();
      renderer = null;
    };
    // Intentionally once per mount; motion/paused flow through refs and
    // the static-frame effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-render a static frame when entering reduced/paused states is
  // handled by the loop above reading refs every frame.

  if (failed) {
    return <WebGLFallback />;
  }
  return (
    <div
      ref={hostRef}
      className="hero-canvas"
      role="img"
      aria-label="Animated 3D scene: a luminous AI neural core above a rotating digital Earth with global connection paths. Illustrative visualization."
      data-testid="hero-scene"
    />
  );
}

/* Client-only Three.js hero canvas: composition, camera, lights,
 * animation loop, resize handling, reduced-motion + pause support,
 * drag/zoom/region-pick interactions, keyboard equivalents, WebGL
 * context-loss handling, and full resource cleanup on unmount. Rendered
 * via next/dynamic with ssr:false so no browser API runs on the
 * server. View state lives in the shared GlobeController so buttons,
 * keyboard, and pointer gestures stay in sync. */

"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { useTranslation } from "../../lib/i18n/context";
import { buildBrain } from "./scene/brain";
import {
  CLICK_MAX_TRAVEL_PX,
  handleGlobeKey,
  PINCH_ZOOM_PER_PX,
  WHEEL_ZOOM_PER_DELTA,
  type GlobeController,
} from "./scene/controls";
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
  controller: GlobeController;
}

export function GlobalHeroScene({ motion, paused, controller }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const motionRef = useRef(motion);
  const pausedRef = useRef(paused);
  const hiddenRef = useRef(false);
  const controllerRef = useRef(controller);
  const [failed, setFailed] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const { t } = useTranslation("landing");
  motionRef.current = motion;
  pausedRef.current = paused;
  controllerRef.current = controller;

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
    let lost = false;
    let lastT = 0;
    const parts: ScenePart[] = [];
    const clock = new THREE.Clock();
    const pointer = new THREE.Vector2(0, 0);
    const ndc = new THREE.Vector2();
    const cameraBase = new THREE.Vector3();
    const lookTarget = new THREE.Vector3(0, -0.3, 0);
    const view = { yaw: 0, pitch: 0 };
    const raycaster = new THREE.Raycaster();

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
    const canvas = renderer.domElement;
    host.appendChild(canvas);

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
    // L-01: assembly runs guarded. No listeners, observers, or frames
    // exist yet at this point (all attach below), so a setup throw can
    // only leak the renderer + canvas, both released here before the
    // branded fallback takes over.
    let stars: ReturnType<typeof buildStars>;
    let earth: ReturnType<typeof buildEarth>;
    let brain: ReturnType<typeof buildBrain>;
    let network: ReturnType<typeof buildNetwork>;
    let orbital: ReturnType<typeof buildOrbital>;
    try {
      stars = buildStars(quality);
      earth = buildEarth(quality, view);
      earth.group.position.y = EARTH_Y;
      brain = buildBrain(quality);
      brain.group.position.y = BRAIN_Y;
      const hubs = REGION_HUBS.map((hub) =>
        latLongToVec3(hub.lat, hub.lon, EARTH_RADIUS * 1.02).add(
          new THREE.Vector3(0, EARTH_Y, 0)
        )
      );
      network = buildNetwork(
        new THREE.Vector3(0, BRAIN_Y - 0.7, 0), hubs, quality
      );
      orbital = buildOrbital(quality);
      orbital.group.position.y = EARTH_Y;
      parts.push(stars, earth, brain, network, orbital);
      parts.forEach((part) => scene.add(part.group));
    } catch {
      renderer.dispose();
      canvas.remove();
      setFailed(true);
      return;
    }

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
      // The safe-area cell is shorter than the old full-hero stage,
      // so the camera sits lower and looks below center: the globe
      // fills the frame instead of sinking to its bottom edge.
      camera.position.set(0, mobile ? 0.4 : 0.1, mobile ? 9.6 : 7.2);
      lookTarget.set(0, mobile ? -0.1 : -0.3, 0);
      camera.lookAt(lookTarget);
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

    // --- Atlas gestures: drag to rotate, wheel/pinch to zoom, tap to
    // pick a region hub. User-driven motion stays available under
    // reduced motion (explicit interaction, like scrolling).
    const activePointers = new Map<number, { x: number; y: number }>();
    let downAt: { x: number; y: number } | null = null;
    let pinchDistance = 0;

    const pick = (clientX: number, clientY: number) => {
      const rect = canvas.getBoundingClientRect();
      ndc.set(
        ((clientX - rect.left) / rect.width) * 2 - 1,
        -(((clientY - rect.top) / rect.height) * 2 - 1)
      );
      raycaster.setFromCamera(ndc, camera);
      const hits = raycaster.intersectObject(earth.group, true);
      const first = hits[0]?.object.userData.hubIndex;
      controllerRef.current.select(
        typeof first === "number" ? first : -1
      );
    };

    const onPointerDown = (event: PointerEvent) => {
      activePointers.set(event.pointerId, {
        x: event.clientX,
        y: event.clientY,
      });
      if (activePointers.size === 1) {
        downAt = { x: event.clientX, y: event.clientY };
        try {
          canvas.setPointerCapture(event.pointerId);
        } catch {
          // Capture unsupported; drag tracking still works.
        }
      } else if (activePointers.size === 2) {
        const [a, b] = [...activePointers.values()] as [
          { x: number; y: number },
          { x: number; y: number },
        ];
        pinchDistance = Math.hypot(a.x - b.x, a.y - b.y);
        downAt = null;
      }
    };
    const onPointerMove = (event: PointerEvent) => {
      const previous = activePointers.get(event.pointerId);
      if (!previous) return;
      activePointers.set(event.pointerId, {
        x: event.clientX,
        y: event.clientY,
      });
      if (activePointers.size === 1) {
        controllerRef.current.addRotation(
          event.clientX - previous.x,
          event.clientY - previous.y
        );
      } else if (activePointers.size === 2) {
        const [a, b] = [...activePointers.values()] as [
          { x: number; y: number },
          { x: number; y: number },
        ];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        controllerRef.current.zoomBy(
          -(distance - pinchDistance) * PINCH_ZOOM_PER_PX
        );
        pinchDistance = distance;
      }
    };
    const endPointer = (event: PointerEvent) => {
      activePointers.delete(event.pointerId);
      if (downAt !== null && activePointers.size === 0) {
        const travel = Math.hypot(
          event.clientX - downAt.x,
          event.clientY - downAt.y
        );
        if (travel <= CLICK_MAX_TRAVEL_PX) pick(event.clientX, event.clientY);
      }
      if (activePointers.size < 2) pinchDistance = 0;
      if (activePointers.size === 0) downAt = null;
    };
    const onWheel = (event: WheelEvent) => {
      // Non-passive: zooming the atlas must not scroll the page.
      event.preventDefault();
      controllerRef.current.zoomBy(event.deltaY * WHEEL_ZOOM_PER_DELTA);
    };
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", endPointer);
    canvas.addEventListener("pointercancel", endPointer);
    canvas.addEventListener("wheel", onWheel, { passive: false });

    const onContextLost = (event: Event) => {
      // Keep the context recoverable; pause rendering until restore.
      event.preventDefault();
      lost = true;
      setContextLost(true);
    };
    const onContextRestored = () => {
      lost = false;
      setContextLost(false);
    };
    canvas.addEventListener("webglcontextlost", onContextLost);
    canvas.addEventListener("webglcontextrestored", onContextRestored);

    const renderFrame = () => {
      if (!renderer || disposed) return;
      const allowMotion =
        !pausedRef.current && motionRef.current === "full";
      const state = controllerRef.current.getState();
      view.yaw = state.yaw;
      view.pitch = state.pitch;
      camera.position.z = cameraBase.z + state.zoom;
      if (allowMotion) {
        const dt = Math.min(clock.getDelta(), 0.05);
        const t = clock.elapsedTime;
        lastT = t;
        parts.forEach((part) => part.update(dt, t));
        // Gentle parallax, disabled under reduced motion.
        camera.position.x +=
          (cameraBase.x + pointer.x * 0.25 - camera.position.x) * 0.04;
        camera.position.y +=
          (cameraBase.y + pointer.y * 0.18 - camera.position.y) * 0.04;
        camera.lookAt(lookTarget);
      } else {
        clock.getDelta();
        // Static frame, but explicit user view offsets still apply.
        earth.update(0, lastT);
      }
      if (!lost) {
        renderer.render(scene, camera);
      }
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
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", endPointer);
      canvas.removeEventListener("pointercancel", endPointer);
      canvas.removeEventListener("wheel", onWheel);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      canvas.removeEventListener("webglcontextrestored", onContextRestored);
      parts.forEach((part) => {
        scene.remove(part.group);
        part.dispose();
      });
      renderer?.dispose();
      renderer?.domElement.remove();
      renderer = null;
    };
    // Intentionally once per mount; motion/paused/controller flow
    // through refs. The static-frame path above reads them every frame.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (handleGlobeKey(event.key, controller, REGION_HUBS.length)) {
      event.preventDefault();
    }
  };

  if (failed) {
    return <WebGLFallback />;
  }
  return (
    <div
      ref={hostRef}
      className="hero-canvas"
      role="group"
      tabIndex={0}
      aria-label="Interactive 3D world atlas: a luminous AI neural core above a rotating digital Earth with global connection paths. Illustrative visualization."
      aria-describedby="globe-hint"
      data-testid="hero-scene"
      onKeyDown={onKeyDown}
    >
      {contextLost && (
        <p className="globe-context-note" role="status">
          {t("globeContextLost")}
        </p>
      )}
    </div>
  );
}

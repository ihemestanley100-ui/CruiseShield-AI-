"use client";

/* Count-up hook: animates 0 → value with rAF, always converging to the
 * exact application value. Reduced-motion users get the final value
 * immediately; no animation ever changes underlying data. */

import { useEffect, useState } from "react";

const DURATION_MS = 900;

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof window.matchMedia !== "function") return false;
  return (
    window.matchMedia("(prefers-reduced-motion: reduce)")?.matches ?? false
  );
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export function useCountUp(value: number): number {
  const [display, setDisplay] = useState(() =>
    prefersReducedMotion() || !Number.isFinite(value) ? value : 0
  );

  useEffect(() => {
    if (prefersReducedMotion() || !Number.isFinite(value)) {
      setDisplay(value);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      // Clamp both ends: a frame timestamp earlier than `start`
      // (mixed clocks) must render 0, never a negative count.
      const t = Math.min(1, Math.max(0, (now - start) / DURATION_MS));
      setDisplay(Math.round(easeOutCubic(t) * value));
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        setDisplay(value);
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return display;
}

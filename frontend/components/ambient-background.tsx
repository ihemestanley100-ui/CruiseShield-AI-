"use client";

/* Decorative ambient background: slow particles + faint links + grid on
 * canvas. Strictly non-interactive (aria-hidden, pointer-events none,
 * behind content) and restrained. Pauses when the tab hides or
 * reduced-motion is requested; renders one static frame then. Cleans
 * up rAF, listeners, and canvas state on unmount. No data shown. */

import { useEffect, useRef } from "react";

const PARTICLES = 42;
const LINK_DIST = 130;
const SPEED = 0.12;

interface Dot {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}

function seeded(i: number, salt: number): number {
  let h = (i + 1) * 2654435761 + salt * 40503;
  h ^= h >> 15;
  h = (h * 2246822519) >>> 0;
  h ^= h >> 13;
  return (h >>> 0) / 4294967295;
}

export function AmbientBackground() {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return; // No canvas 2D: leave the plain background.
    const reduced =
      typeof window.matchMedia === "function" &&
      (window.matchMedia("(prefers-reduced-motion: reduce)")?.matches ??
        false);

    let w = 0;
    let h = 0;
    let dots: Dot[] = [];
    let raf = 0;
    let running = true;

    function resize() {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas!.width = Math.floor(w * dpr);
      canvas!.height = Math.floor(h * dpr);
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      dots = Array.from({ length: PARTICLES }, (_, i) => ({
        x: seeded(i, 1) * w,
        y: seeded(i, 2) * h,
        vx: (seeded(i, 3) - 0.5) * SPEED,
        vy: (seeded(i, 4) - 0.5) * SPEED,
        r: 1 + seeded(i, 5) * 1.6,
      }));
    }

    function frame() {
      if (!running) return;
      ctx!.clearRect(0, 0, w, h);
      // Faint grid.
      ctx!.strokeStyle = "rgba(50, 143, 234, 0.07)";
      ctx!.lineWidth = 1;
      const step = 56;
      ctx!.beginPath();
      for (let x = 0.5; x < w; x += step) {
        ctx!.moveTo(x, 0);
        ctx!.lineTo(x, h);
      }
      for (let y = 0.5; y < h; y += step) {
        ctx!.moveTo(0, y);
        ctx!.lineTo(w, y);
      }
      ctx!.stroke();
      // Links then dots.
      ctx!.strokeStyle = "rgba(38, 215, 255, 0.14)";
      for (let i = 0; i < dots.length; i++) {
        for (let j = i + 1; j < dots.length; j++) {
          const dx = dots[i].x - dots[j].x;
          const dy = dots[i].y - dots[j].y;
          if (dx * dx + dy * dy < LINK_DIST * LINK_DIST) {
            ctx!.beginPath();
            ctx!.moveTo(dots[i].x, dots[i].y);
            ctx!.lineTo(dots[j].x, dots[j].y);
            ctx!.stroke();
          }
        }
      }
      ctx!.fillStyle = "rgba(234, 246, 255, 0.5)";
      for (const d of dots) {
        ctx!.beginPath();
        ctx!.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx!.fill();
        d.x += d.vx;
        d.y += d.vy;
        if (d.x < 0 || d.x > w) d.vx *= -1;
        if (d.y < 0 || d.y > h) d.vy *= -1;
      }
      if (!reduced) raf = requestAnimationFrame(frame);
    }

    function onVisibility() {
      const hidden = document.hidden;
      if (hidden) {
        running = false;
        cancelAnimationFrame(raf);
      } else if (!running) {
        running = true;
        if (!reduced) raf = requestAnimationFrame(frame);
        else frame();
      }
    }

    resize();
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVisibility);
    frame();

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      className="ambient-canvas"
      aria-hidden="true"
      data-testid="ambient-background"
    />
  );
}

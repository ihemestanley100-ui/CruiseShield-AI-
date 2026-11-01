/* Cinematic landing composition: hero scene, copy, panels,
 * strips, and controls. The 3D canvas loads client-side only. */

"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import {
  LandingCta,
  LandingHeroCopy,
  LandingNav,
} from "./LandingChrome";
import { AudioControl, MotionControl } from "./LandingControls";
import {
  CoveragePanel,
  IntelligencePanel,
  ModuleCards,
} from "./LandingPanels";
import { CapabilityStrip, GlobalMetrics } from "./LandingStrips";
import { WebGLFallback } from "./WebGLFallback";

const GlobalHeroScene = dynamic(
  () => import("./GlobalHeroScene").then((mod) => mod.GlobalHeroScene),
  { ssr: false, loading: () => <WebGLFallback /> }
);

export function GlobalLandingPage() {
  const [motion, setMotion] = useState<"full" | "reduced">("full");
  const [paused, setPaused] = useState(false);
  const blipRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      setMotion("reduced");
    }
  }, []);

  return (
    <div className="landing">
      <LandingNav />
      <main>
        <section className="landing-hero" aria-labelledby="landing-h1">
          <div className="landing-hero-stage">
            <GlobalHeroScene motion={motion} paused={paused} />
            <div className="landing-hero-overlay">
              <LandingHeroCopy />
              <div className="landing-core-label" aria-hidden="true">
                <strong>CruiseShield AI™</strong>
                <span>Global Intelligence Core</span>
              </div>
            </div>
            <IntelligencePanel />
            <CoveragePanel />
            <ModuleCards />
            <LandingCta
              onActivate={() => {
                blipRef.current?.();
              }}
            />
            <div className="landing-controls">
              <MotionControl
                motion={motion}
                paused={paused}
                onMotion={setMotion}
                onPaused={setPaused}
              />
              <AudioControl onBlipRef={blipRef} />
            </div>
          </div>
        </section>
        <CapabilityStrip />
        <GlobalMetrics />
      </main>
      <footer className="landing-footer">
        <p className="muted">
          Demonstration experience · synthetic data · illustrative network
          visuals ·{" "}
          <a href="/demo">Enter the interactive demo</a>
        </p>
      </footer>
    </div>
  );
}

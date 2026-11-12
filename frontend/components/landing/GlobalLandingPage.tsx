/* Cinematic landing composition: hero copy, atlas row (side panels
 * flanking a dedicated globe safe area), CTA, controls, then the
 * capability sections below the fold. The 3D canvas loads
 * client-side only. Nothing overlaps the central atlas: panels and
 * cards occupy their own grid cells, never absolute layers. */

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
import { GlobeControls } from "./GlobeControls";
import { IntelligenceFrameworkPanel } from "./IntelligenceFrameworkPanel";
import { GlobeController } from "./scene/controls";
import { WebGLFallback } from "./WebGLFallback";
import { SkipLink } from "../skip-link";
import { useTranslation } from "../../lib/i18n/context";

const GlobalHeroScene = dynamic(
  () => import("./GlobalHeroScene").then((mod) => mod.GlobalHeroScene),
  { ssr: false, loading: () => <WebGLFallback /> }
);

export function GlobalLandingPage() {
  const { t } = useTranslation("landing");
  const [motion, setMotion] = useState<"full" | "reduced">("full");
  const [paused, setPaused] = useState(false);
  const [controller] = useState(() => new GlobeController());
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
      <SkipLink />
      <LandingNav />
      <main id="main-content" tabIndex={-1}>
        <section className="landing-hero" aria-labelledby="landing-h1">
          <LandingHeroCopy />
          <div className="landing-atlas-row">
            <IntelligencePanel />
            <div className="landing-safe-area">
              <GlobalHeroScene
                motion={motion}
                paused={paused}
                controller={controller}
              />
              <div className="landing-core-label" aria-hidden="true">
                <strong>CruiseShield AI™</strong>
                <span>Global Intelligence Core</span>
              </div>
              <GlobeControls controller={controller} />
            </div>
            <CoveragePanel />
          </div>
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
          <IntelligenceFrameworkPanel />
        </section>
        <div className="landing-modules-section">
          <ModuleCards />
        </div>
        <CapabilityStrip />
        <GlobalMetrics />
      </main>
      <footer className="landing-footer">
        <p className="muted">
          {t("footerNote")}
          <a href="/platform">{t("footerLink")}</a>
        </p>
      </footer>
    </div>
  );
}

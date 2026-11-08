"use client";

import Link from "next/link";
import { useTranslation } from "../../lib/i18n/context";

/* Graceful fallback when WebGL is unavailable: full brand, headline,
 * and platform entry remain usable with no 3D required. */
export function WebGLFallback() {
  const { t } = useTranslation("landing");
  return (
    <div className="hero-fallback" data-testid="webgl-fallback">
      <div className="hero-fallback-core" aria-hidden="true">
        <span className="hero-fallback-ring" />
        <span className="hero-fallback-ring small" />
        <span className="hero-fallback-dot" />
      </div>
      <p className="muted">{t("fallbackNote")}</p>
      <p>
        <Link className="landing-cta" href="/platform">
          {t("cta")} <span aria-hidden="true">→</span>
        </Link>
      </p>
    </div>
  );
}

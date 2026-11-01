import Link from "next/link";

/* Graceful fallback when WebGL is unavailable: full brand, headline,
 * and demo entry remain usable with no 3D required. */
export function WebGLFallback() {
  return (
    <div className="hero-fallback" data-testid="webgl-fallback">
      <div className="hero-fallback-core" aria-hidden="true">
        <span className="hero-fallback-ring" />
        <span className="hero-fallback-ring small" />
        <span className="hero-fallback-dot" />
      </div>
      <p className="muted">
        Interactive 3D is unavailable in this browser. The full demo
        experience remains open.
      </p>
      <p>
        <Link className="landing-cta" href="/demo">
          Explore CruiseShield AI™ <span aria-hidden="true">→</span>
        </Link>
      </p>
    </div>
  );
}

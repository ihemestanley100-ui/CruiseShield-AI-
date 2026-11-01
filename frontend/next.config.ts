import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Temporary verification override (reverted after the Phase 2B rerun).
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // Render staging (SEC-010): baseline secure headers. No CSP: the Three.js
  // landing uses inline scripts/styles that a strict policy would break;
  // revisit with a nonce-based policy before any production claim.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;

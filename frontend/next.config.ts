import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // J3-P10: Phase 2B temporary distDir override removed; default .next.
  async headers() {
    // R07: Content Security Policy. script/style 'unsafe-inline' is
    // required by Next.js bootstrapping + the theme/locale init scripts
    // (no nonce infrastructure); React auto-escaping + the XSS test
    // suite remain the primary injection defense. connect-src allows
    // exactly this build's API origin (build-time baked, per-env
    // correct). Verified route-by-route in Edge (see
    // docs/FINAL_SECURITY_AUDIT.md); any violation fails loudly in
    // the console rather than silently.
    const apiOrigin =
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      `connect-src 'self' ${apiOrigin}`,
      "object-src 'none'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
    ].join("; ");
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
          // R09-F4: HSTS. Static config cannot see the request scheme,
          // so this is served on HTTP too — browsers MUST ignore HSTS
          // over insecure transport (RFC 6797 8.1), keeping local
          // http://localhost dev unaffected. No includeSubDomains
          // (shared parent domains on managed hosting), no preload.
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000",
          },
          { key: "Content-Security-Policy", value: csp },
        ],
      },
    ];
  },
};

export default nextConfig;

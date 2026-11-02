import { describe, expect, it } from "vitest";
import nextConfig from "./next.config";

describe("next.config secure headers", () => {
  it("serves the documented baseline on every route", async () => {
    const rules = await nextConfig.headers!();
    expect(rules).toHaveLength(1);
    expect(rules[0].source).toBe("/:path*");
    const values = Object.fromEntries(
      rules[0].headers.map((h) => [h.key, h.value]),
    );
    expect(values).toMatchObject({
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    });
  });

  it("serves a CSP whose connect-src tracks the build API origin", async () => {
    const rules = await nextConfig.headers!();
    const values = Object.fromEntries(
      rules[0].headers.map((h) => [h.key, h.value]),
    );
    const csp: string = values["Content-Security-Policy"];
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).not.toContain("*");
    // Build default (no env override in test): localhost API origin.
    expect(csp).toContain(
      "connect-src 'self' http://127.0.0.1:8000",
    );
  });
});

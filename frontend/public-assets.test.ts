import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { describe, expect, it } from "vitest";

/* Served-asset manifest: every static file the layout metadata and
 * shell reference must exist in public/. This test would have caught
 * the missing /favicon.ico 404 (R-09 remediation follow-up). */
const root = join(dirname(fileURLToPath(import.meta.url)), "public");

const REQUIRED = [
  "favicon.ico",
  "icons/favicon-16x16.png",
  "icons/favicon-32x32.png",
  "icons/favicon-48x48.png",
  "icons/apple-touch-icon.png",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "assets/cruiseshield-logo-original.png",
];

describe("served static assets", () => {
  it.each(REQUIRED)("ships %s", (rel) => {
    expect(existsSync(join(root, rel))).toBe(true);
  });
});

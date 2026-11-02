import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const PUBLIC_ICONS = [
  "favicon-16x16.png",
  "favicon-32x32.png",
  "favicon-48x48.png",
  "apple-touch-icon.png",
  "icon-192.png",
  "icon-512.png",
];

describe("brand icons and metadata wiring", () => {
  it("ships every referenced icon file with real bytes", () => {
    for (const name of PUBLIC_ICONS) {
      const size = statSync(
        join(process.cwd(), "public", "icons", name),
      ).size;
      expect(size, name).toBeGreaterThan(0);
    }
    expect(
      statSync(join(process.cwd(), "app", "favicon.ico")).size,
    ).toBeGreaterThan(0);
    expect(
      statSync(join(process.cwd(), "app", "icon.png")).size,
    ).toBeGreaterThan(0);
  });

  it("layout metadata references the shipped icon paths", () => {
    const layout = readFileSync(
      join(process.cwd(), "app", "layout.tsx"),
      "utf-8",
    );
    for (const path of [
      "/icons/favicon-16x16.png",
      "/icons/favicon-32x32.png",
      "/icons/favicon-48x48.png",
      "/icons/apple-touch-icon.png",
      "/icons/icon-512.png",
      "/favicon.ico",
    ]) {
      expect(layout, path).toContain(path);
    }
    expect(layout).toContain("metadataBase");
  });
});

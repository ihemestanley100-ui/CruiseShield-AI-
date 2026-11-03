import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { coverageFor, englishKeyPaths } from "./coverage";

/* Key-inventory dump freshness: docs/UGLS_KEY_INVENTORY_GENERATED.txt
 * must match the dictionaries exactly (stale dump fails: re-run with
 * UGLS_REGEN_KIT=1, same command as the review kit). Built from the
 * production coverage machinery: sorted English paths plus per-locale
 * missing lists in registry order. */

const DUMP_TAGS = [
  "fr",
  "ar",
  "ig",
  "yo",
  "ha",
  "pt",
  "es",
  "zh",
  "hi",
  "sw",
  "ja",
];

const DUMP_FILE = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "..",
  "docs",
  "UGLS_KEY_INVENTORY_GENERATED.txt"
);

const REGEN = process.env.UGLS_REGEN_KIT === "1";

function buildDump(): string {
  const keys = [...englishKeyPaths()].sort();
  const lines = [`EN_KEYS=${keys.length}`, ...keys];
  for (const tag of DUMP_TAGS) {
    const missing = new Set(coverageFor(tag).missing);
    const ordered = keys.filter((k) => missing.has(k));
    lines.push(`--- MISSING ${tag} (${ordered.length}) ---`, ...ordered);
  }
  return lines.join("\n") + "\n";
}

describe("key inventory dump", () => {
  it("matches the dictionaries", () => {
    const dump = buildDump();
    if (REGEN) {
      writeFileSync(DUMP_FILE, dump);
      return;
    }
    if (!existsSync(DUMP_FILE)) {
      throw new Error("missing inventory dump — regenerate with UGLS_REGEN_KIT=1");
    }
    expect(readFileSync(DUMP_FILE, "utf8")).toBe(dump);
  });
});

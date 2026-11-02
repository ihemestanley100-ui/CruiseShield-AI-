import { describe, expect, it } from "vitest";
import { coverageFor, coverageSummary, englishKeyPaths } from "./coverage";
import { getLocaleMeta, isHumanVerified } from "./meta";

const DRAFT_TAGS = [
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

describe("translation coverage", () => {
  it("defines a non-trivial English source key set", () => {
    expect(englishKeyPaths().length).toBeGreaterThan(100);
  });

  it("holds every dictionaried locale at exact key parity with English", () => {
    // Every dictionaried locale drafts every converted key: any new en
    // key without translations fails here by design.
    for (const tag of ["fr", "ar", ...DRAFT_TAGS]) {
      const coverage = coverageFor(tag);
      expect(coverage.missing).toEqual([]);
      expect(coverage.coverage).toBe(1);
      expect(coverage.keys).toBe(coverage.total);
    }
  });

  it("reports zero coverage for undictionaried locales", () => {
    const coverage = coverageFor("zu");
    expect(coverage.keys).toBe(0);
    expect(coverage.coverage).toBe(0);
    expect(coverage.missing.length).toBeGreaterThan(100);
  });

  it("keeps full drafts machine-drafted, never human-verified", () => {
    // UGLS final: all 571 keys drafted per locale, but unreviewed
    // output must never report as human-verified.
    for (const tag of ["fr", "ar", ...DRAFT_TAGS]) {
      expect(getLocaleMeta(tag)?.review).toBe("machine-drafted");
      expect(isHumanVerified(tag)).toBe(false);
    }
    expect(isHumanVerified("en")).toBe(true);
  });

  it("summarizes translated/partial/unavailable counts honestly", () => {
    const summary = coverageSummary();
    expect(summary.totalKeys).toBeGreaterThan(100);
    expect(summary.translated).toBe(3); // en, en-GB, en-NG
    // fr, ar (complete) + ig, yo, ha, pt, es, zh, hi, sw, ja (drafts).
    expect(summary.partial).toBe(11);
    expect(summary.unavailable).toBeGreaterThan(200);
  });
});

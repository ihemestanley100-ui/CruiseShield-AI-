import { beforeEach, describe, expect, it } from "vitest";
import {
  clearMissingKeys,
  flattenKeys,
  getMissingKeys,
  interpolate,
  lookup,
  lookupForms,
  lookupList,
  selectPlural,
} from "./dictionaries";

describe("dictionaries", () => {
  beforeEach(() => {
    clearMissingKeys();
  });

  it("resolves English keys exactly", () => {
    expect(lookup("en", "nav.commandCenter").text).toBe("Command Center");
    expect(lookup("en", "auth.signIn").text).toBe("Sign in");
    expect(lookup("en", "decision.record").text).toBe("Record decision");
  });

  it("resolves French and Arabic keys", () => {
    expect(lookup("fr", "nav.commandCenter").text).toBe("Centre de commandement");
    expect(lookup("ar", "auth.signIn").text).toBe("تسجيل الدخول");
    expect(lookup("ar", "decision.record").text).toBe("تسجيل القرار");
  });

  it("falls back through regional variants to the base dictionary", () => {
    expect(lookup("fr-CA", "nav.cases").text).toBe("Dossiers");
    expect(lookup("ar-EG", "nav.cases").text).toBe("القضايا");
    expect(lookup("en-NG", "nav.cases").text).toBe("Cases");
  });

  it("falls back to English for undictionaried locales, flagged", () => {
    const result = lookup("zu", "nav.cases");
    expect(result.text).toBe("Cases");
    expect(result.fellBack).toBe(true);
    // Whole-locale fallback is a known status (coverage report + selector
    // badge), not a per-key gap: the ledger stays quiet by design.
    expect(getMissingKeys()).toEqual([]);
  });

  it("never silently invents text for keys missing even in English", () => {
    const result = lookup("en", "nav.noSuchKey");
    expect(result.text).toBe("[nav.noSuchKey]");
    expect(getMissingKeys()).toContain("en:nav.noSuchKey");
  });

  it("interpolates {vars} and preserves unknown placeholders", () => {
    expect(interpolate("{role} · active", { role: "admin" })).toBe("admin · active");
    expect(lookup("en", "nav.roleContext", { role: "auditor" }).text).toBe(
      "auditor · active"
    );
    expect(interpolate("{missing}", {})).toBe("{missing}");
  });

  it("resolves translated lists for every dictionaried locale", () => {
    // UGLS final: all nine drafts ship translated lists, so no
    // per-key gap is recorded for any dictionaried locale.
    const firstSteps: Record<string, string> = {
      en: "DETECT",
      fr: "DÉTECTER",
      ig: "CHỌPỤTA",
      yo: "ṢÀWÁRÍ",
      ha: "GANO",
      pt: "DETETAR",
      es: "DETECTAR",
      zh: "检测",
      hi: "पता लगाएँ",
      sw: "GUNDUA",
      ja: "検出",
    };
    for (const [tag, first] of Object.entries(firstSteps)) {
      const journey = lookupList(tag, "landing.journey");
      expect(journey).toHaveLength(8);
      expect(journey[0]).toBe(first);
    }
    expect(lookupList("ar", "landing.journey")).toHaveLength(8);
    expect(getMissingKeys()).toEqual([]);
    expect(lookupList("en", "landing.noSuchList")).toEqual([]);
  });

  it("selects plurals per locale via Intl.PluralRules", () => {
    const forms = { one: "{count} item", other: "{count} items" };
    expect(selectPlural("en", 1, forms)).toBe("1 item");
    expect(selectPlural("en", 5, forms)).toBe("5 items");
    const arForms = {
      zero: "لا عناصر",
      one: "عنصر واحد",
      two: "عنصران",
      few: "{count} عناصر",
      many: "{count} عنصرًا",
      other: "{count} عنصر",
    };
    expect(selectPlural("ar", 0, arForms)).toBe("لا عناصر");
    expect(selectPlural("ar", 2, arForms)).toBe("عنصران");
    expect(selectPlural("ar", 5, arForms)).toBe("5 عناصر");
    // Missing categories degrade to "other", never to nothing.
    expect(selectPlural("ar", 2, { other: "{count} x" })).toBe("2 x");
  });

  it("interpolates {count} in every shipped plural template", () => {
    // Regression: droppedEdges templates once used {n}, which tp()
    // never supplies — the count rendered raw. Every plural template
    // must use {count} (auto-supplied) plus explicitly-passed vars.
    const tags = [
      "en",
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
    for (const key of [
      "audit.events",
      "command.activityEvents",
      "graph.relationships",
      "graph.droppedEdges",
      "intel.findingsCount",
      "intel.obsCount",
      "intel.accountCount",
      "intel.candidateFindings",
    ]) {
      for (const tag of tags) {
        const forms = lookupForms(tag, key);
        expect(Object.keys(forms).length).toBeGreaterThan(0);
        for (const template of Object.values(forms)) {
          // Note: zero/one/two forms may legitimately omit {count}
          // (e.g. Arabic "no events"); only the raw {n} leak is banned.
          expect(template).not.toMatch(/\{n\}/);
        }
      }
    }
    const frDrop = lookupForms("fr", "graph.droppedEdges");
    expect(
      interpolate(selectPlural("fr", 1, frDrop), { ids: "edge_bad" })
    ).toBe("1 arête masquée : extrémité inconnue (edge_bad).");
    const arDrop = lookupForms("ar", "graph.droppedEdges");
    expect(interpolate(selectPlural("ar", 5, arDrop), { ids: "edge_bad" })).toBe(
      "5 حواف مخفية: الطرف غير معروف (edge_bad)."
    );
  });

  it("flattens nested dictionaries and arrays to key paths", () => {
    const keys = flattenKeys({ a: { b: "x" }, c: ["y", "z"] } as never);
    expect(keys.sort()).toEqual(["a.b", "c.0", "c.1"]);
  });
});

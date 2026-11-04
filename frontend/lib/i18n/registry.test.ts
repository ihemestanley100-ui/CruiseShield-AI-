import { describe, expect, it } from "vitest";
import {
  LANGUAGES,
  LANGUAGE_MAP,
  RTL_BASE_LANGS,
  getLanguage,
  isRtl,
  matchBrowserLocales,
  resolveDictionaryTag,
} from "./registry";

describe("language registry", () => {
  it("covers the full ISO 639-1 set plus variants and indigenous additions", () => {
    // 184 ISO 639-1 codes + regional variants + 639-2/3 additions.
    expect(LANGUAGES.length).toBeGreaterThan(200);
  });

  it("has unique BCP 47 tags that all parse via Intl.Locale", () => {
    const tags = LANGUAGES.map((entry) => entry.tag);
    expect(new Set(tags).size).toBe(tags.length);
    for (const tag of tags) {
      expect(() => new Intl.Locale(tag)).not.toThrow();
    }
  });

  it("gives every entry a native name, exonym, family and ISO code", () => {
    for (const entry of LANGUAGES) {
      expect(entry.native.trim().length).toBeGreaterThan(0);
      expect(entry.english.trim().length).toBeGreaterThan(0);
      expect(entry.family.trim().length).toBeGreaterThan(0);
      expect(entry.iso.trim().length).toBeGreaterThanOrEqual(2);
      expect(entry.tag.startsWith(entry.iso)).toBe(true);
    }
  });

  it("includes African, European, Asian, Middle Eastern and Indigenous families", () => {
    const families = new Set(LANGUAGES.map((entry) => entry.family));
    for (const family of [
      "Niger-Congo",
      "Afro-Asiatic",
      "Indo-European",
      "Sino-Tibetan",
      "Austronesian",
      "Turkic",
      "Dravidian",
      "Quechuan",
      "Iroquoian",
      "Eskimo-Aleut",
      "Na-Dene",
    ]) {
      expect(families.has(family)).toBe(true);
    }
  });

  it("flags right-to-left scripts and keeps LTR for the rest", () => {
    for (const tag of ["ar", "ar-EG", "fa", "he", "ur", "yi", "ps", "sd", "ug", "dv"]) {
      expect(isRtl(tag)).toBe(true);
    }
    for (const tag of ["en", "fr", "de", "es", "zh-Hans", "yo", "sw", "hi"]) {
      expect(isRtl(tag)).toBe(false);
    }
    expect(isRtl("xx-unknown")).toBe(false);
  });

  it("keeps RTL_BASE_LANGS in sync with the registry", () => {
    const expected = [
      ...new Set(
        LANGUAGES.filter((entry) => entry.rtl).map(
          (entry) => entry.tag.split("-")[0] as string
        )
      ),
    ].sort();
    expect([...RTL_BASE_LANGS]).toEqual(expected);
  });

  it("distinguishes translated, partial and unavailable languages", () => {
    expect(getLanguage("en")?.status).toBe("translated");
    expect(getLanguage("en-NG")?.status).toBe("translated");
    expect(getLanguage("fr")?.status).toBe("partial");
    expect(getLanguage("ar")?.status).toBe("partial");
    // Draft locales: dictionaried at full key parity but unreviewed
    // (machine-drafted), so they stay partial, never translated.
    for (const tag of ["ig", "yo", "ha", "pt", "es", "zh", "hi", "sw", "ja"]) {
      expect(getLanguage(tag)?.status).toBe("partial");
    }
    expect(getLanguage("de")?.status).toBe("unavailable");
    const unavailable = LANGUAGES.filter((l) => l.status === "unavailable").length;
    expect(unavailable).toBeGreaterThan(200);
  });

  it("resolves dictionary tags through BCP 47 fallback", () => {
    const available = new Set(["en", "fr", "ar"]);
    expect(resolveDictionaryTag("fr-CA", available)).toBe("fr");
    expect(resolveDictionaryTag("ar-EG", available)).toBe("ar");
    expect(resolveDictionaryTag("en-GB", available)).toBe("en");
    expect(resolveDictionaryTag("de", available)).toBe("en");
    expect(resolveDictionaryTag("xx", available)).toBe("en");
  });

  it("matches browser locale lists against the registry", () => {
    expect(matchBrowserLocales(["yo-NG", "yo", "en"])).toBe("yo");
    expect(matchBrowserLocales(["fr-CA", "en"])).toBe("fr-CA");
    expect(matchBrowserLocales(["pt-PT", "es"])).toBe("pt-PT");
    expect(matchBrowserLocales(["xx", "de-AT"])).toBe("de");
    expect(matchBrowserLocales(["xx"])).toBe("en");
    expect(matchBrowserLocales([])).toBe("en");
  });

  it("exposes a map consistent with the list", () => {
    expect(LANGUAGE_MAP.size).toBe(LANGUAGES.length);
    expect(LANGUAGE_MAP.get("ha-Arab")?.rtl).toBe(true);
  });
});

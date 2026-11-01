import { beforeEach, describe, expect, it } from "vitest";
import { STORAGE_KEY, readStoredMode, resolveTheme } from "./theme";

describe("resolveTheme", () => {
  it("pins explicit dark and light", () => {
    expect(resolveTheme("dark", true)).toBe("dark");
    expect(resolveTheme("dark", false)).toBe("dark");
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("light", false)).toBe("light");
  });

  it("follows the system preference on system", () => {
    expect(resolveTheme("system", true)).toBe("light");
    expect(resolveTheme("system", false)).toBe("dark");
  });
});

describe("readStoredMode", () => {
  beforeEach(() => localStorage.clear());

  it("defaults to system", () => {
    expect(readStoredMode()).toBe("system");
  });

  it("rejects unknown stored values", () => {
    localStorage.setItem(STORAGE_KEY, "neon");
    expect(readStoredMode()).toBe("system");
  });

  it("reads stored modes", () => {
    for (const mode of ["dark", "light", "system"] as const) {
      localStorage.setItem(STORAGE_KEY, mode);
      expect(readStoredMode()).toBe(mode);
    }
  });
});

import { describe, expect, it } from "vitest";
import {
  formatDate,
  formatMoney,
  formatNumber,
  formatRelative,
} from "./format";

describe("locale formatting", () => {
  it("groups numbers per locale", () => {
    expect(formatNumber("en", 480000)).toBe("480,000");
    expect(formatNumber("fr", 480000)).toContain("480");
    // Arabic-Indic digits for ar (falls back gracefully if ICU lacks them).
    expect(formatNumber("ar", 480000).length).toBeGreaterThan(0);
  });

  it("formats money from integer minor units like the backend rule", () => {
    expect(formatMoney("en", 48000000, "NGN")).toBe("₦480,000");
    expect(formatMoney("fr", 48000000, "NGN")).toContain("₦");
    expect(formatMoney("en", 150, "USD")).toContain("2");
  });

  it("formats dates per locale", () => {
    const day = formatDate("en", "2026-10-27T10:00:00Z", {
      dateStyle: "medium",
    });
    expect(day).toContain("2026");
    const frDay = formatDate("fr", "2026-10-27T10:00:00Z", {
      dateStyle: "medium",
    });
    expect(frDay).toContain("2026");
    expect(frDay).not.toBe(day);
  });

  it("formats relative time per locale", () => {
    expect(formatRelative("en", -1, "day")).toContain("yesterday");
    expect(formatRelative("fr", -1, "day")).not.toBe("");
  });

  it("falls back to English on garbage tags, never throws", () => {
    expect(formatNumber("xx", 42)).toBe("42");
    expect(formatMoney("xx", 100, "NGN")).toBe("₦1");
    expect(() => formatDate("xx", "2026-01-01T00:00:00Z")).not.toThrow();
    expect(() => formatRelative("xx", 3, "day")).not.toThrow();
  });

  it("renders unparseable date input verbatim, never Invalid Date", () => {
    expect(
      formatDate("en", "10:00", { dateStyle: "medium", timeStyle: "short" })
    ).toBe("10:00");
    expect(formatDate("fr", "not a date")).toBe("not a date");
  });
});

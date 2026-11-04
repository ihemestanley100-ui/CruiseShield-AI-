import { describe, expect, it } from "vitest";
import { formatKobo } from "./format";

describe("formatKobo", () => {
  it("keeps historic en-US output by default", () => {
    expect(formatKobo(48000000)).toBe("₦480,000");
    expect(formatKobo(150)).toBe("₦2");
    expect(formatKobo(48000000, "USD")).toBe("USD 480,000");
  });

  it("groups per the caller's locale tag", () => {
    expect(formatKobo(48000000, "NGN", "fr")).toContain("₦");
    expect(formatKobo(48000000, "NGN", "fr")).not.toBe("₦480,000");
  });

  it("falls back to English on garbage tags, never throws", () => {
    expect(formatKobo(48000000, "NGN", "!!")).toBe("₦480,000");
  });
});

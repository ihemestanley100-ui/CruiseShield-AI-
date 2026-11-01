import { describe, expect, it } from "vitest";
import { maskIp } from "./privacy";

describe("maskIp", () => {
  it("masks the last IPv4 octet", () => {
    expect(maskIp("192.168.1.10")).toBe("192.168.1.\u2022");
  });

  it("truncates IPv6 to four groups plus a mask", () => {
    expect(maskIp("2001:0db8:85a3:0000:0000:8a2e:0370:7334")).toBe(
      "2001:0db8:85a3:0000:\u2022"
    );
  });

  it("returns unknown for missing or invalid input", () => {
    expect(maskIp(null)).toBe("unknown");
    expect(maskIp(undefined)).toBe("unknown");
    expect(maskIp("")).toBe("unknown");
    expect(maskIp("999.1.1.1")).toBe("unknown");
    expect(maskIp("not-an-ip")).toBe("unknown");
    expect(maskIp("zzzz::1")).toBe("unknown");
  });
});

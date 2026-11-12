import { describe, expect, it } from "vitest";
import { resolveMetadataBase } from "./site-url";

describe("resolveMetadataBase", () => {
  it("resolves a deployed https origin", () => {
    const base = resolveMetadataBase("https://cruiseshield-platform.vercel.app");
    expect(base?.href).toBe("https://cruiseshield-platform.vercel.app/");
  });

  it("accepts http origins and trims whitespace", () => {
    const base = resolveMetadataBase("  http://127.0.0.1:3000\n");
    expect(base?.href).toBe("http://127.0.0.1:3000/");
  });

  it("preserves relative URLs when unset or blank", () => {
    expect(resolveMetadataBase(undefined)).toBeUndefined();
    expect(resolveMetadataBase("")).toBeUndefined();
    expect(resolveMetadataBase("   ")).toBeUndefined();
  });

  it("rejects garbage and non-web schemes", () => {
    expect(resolveMetadataBase("not a url")).toBeUndefined();
    expect(resolveMetadataBase("ftp://files.example/x")).toBeUndefined();
    expect(
      resolveMetadataBase("javascript:alert(1)"),
    ).toBeUndefined();
  });
});

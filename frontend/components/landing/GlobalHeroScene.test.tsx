import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GlobalHeroScene } from "./GlobalHeroScene";

vi.mock("./scene/webgl", () => ({
  isWebGLAvailable: () => false,
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

describe("GlobalHeroScene", () => {
  it("renders an accessible fallback when WebGL is unavailable", () => {
    render(<GlobalHeroScene motion="full" paused={false} />);
    expect(screen.getByTestId("webgl-fallback")).toBeTruthy();
    const cta = screen.getByRole("link", { name: /Explore CruiseShield AI/ });
    expect(cta.getAttribute("href")).toBe("/demo");
  });

  it("reserves the bottom stage so the fallback clears the modules row (D-013)", () => {
    // jsdom cannot do layout; pin the measured fix instead: .hero-fallback
    // must keep a bottom inset (>= 12rem) so its CTA cannot reach the
    // bottom-anchored .landing-modules row. Fails if reverted to inset: 0.
    const css = readFileSync(
      join(process.cwd(), "styles", "landing.css"),
      "utf-8"
    );
    const block = css.match(/\.hero-fallback\s*\{([^}]*)\}/)?.[1] ?? "";
    const inset = block.match(/inset:\s*0\s+0\s+([\d.]+)rem/)?.[1];
    expect(inset, ".hero-fallback must reserve bottom stage space").toBeDefined();
    expect(Number(inset)).toBeGreaterThanOrEqual(12);
  });
});

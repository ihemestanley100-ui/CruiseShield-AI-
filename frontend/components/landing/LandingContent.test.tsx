import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GlobalLandingPage } from "./GlobalLandingPage";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("./GlobalHeroScene", () => ({
  GlobalHeroScene: ({ motion, paused }: { motion: string; paused: boolean }) => (
    <div data-testid="hero-stub" data-motion={motion} data-paused={String(paused)} />
  ),
}));

beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  );
});

describe("GlobalLandingPage", () => {
  it("renders brand, hero copy, journey, and demo CTAs", () => {
    render(<GlobalLandingPage />);
    expect(screen.getAllByText("CruiseShield AI™").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "A Safer Financial World" })
    ).toBeTruthy();
    for (const step of ["DETECT", "CONNECT", "EXPLAIN", "PREVENT", "PROTECT"]) {
      expect(screen.getByText(step)).toBeTruthy();
    }
    // Hero CTA + WebGL-fallback CTA both target /demo (jsdom has no WebGL).
    const ctas = screen.getAllByRole("link", { name: /Explore CruiseShield AI/ });
    expect(ctas.length).toBeGreaterThanOrEqual(1);
    for (const cta of ctas) {
      expect(cta.getAttribute("href")).toBe("/demo");
    }
    expect(screen.getByRole("link", { name: "Enter Demo" })).toHaveProperty(
      "href"
    );
  });

  it("renders intelligence panels, modules, regions, and strips", () => {
    render(<GlobalLandingPage />);
    expect(
      screen.getByRole("heading", { name: "Global Intelligence" })
    ).toBeTruthy();
    expect(
      screen.getAllByText("Transaction Monitoring").length
    ).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Evidence and Audit")).toBeTruthy();
    expect(screen.getByText("Satellite Intelligence")).toBeTruthy();
    expect(screen.getByText("Secure Infrastructure")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Global Intelligence Regions" })
    ).toBeTruthy();
    expect(screen.getByText("Illustrative Network View")).toBeTruthy();
    expect(screen.getByText("Orbital Layer")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "One platform, ten intelligence layers" })
    ).toBeTruthy();
    const strip = screen
      .getByRole("heading", { name: "One platform, ten intelligence layers" })
      .closest("section");
    expect(within(strip as HTMLElement).getAllByRole("link")).toHaveLength(11);
    expect(screen.getAllByText("Human Oversight").length).toBeGreaterThanOrEqual(
      2
    );
    expect(
      screen.getByText("One Platform. A Safer Financial Future. For Everyone.")
    ).toBeTruthy();
  });

  it("routes capability cards only to real demo screens", () => {
    render(<GlobalLandingPage />);
    const strip = screen
      .getByRole("heading", { name: "One platform, ten intelligence layers" })
      .closest("section");
    const hrefs = within(strip as HTMLElement)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
    const allowed = new Set([
      "/demo",
      "/network/txn_84721",
      "/investigations/inv_84721",
      "/investigations/inv_84721#ai-h",
      "/cases/case_84721",
      "/replay/scn_primary",
    ]);
    for (const href of hrefs) {
      expect(allowed.has(href ?? "")).toBe(true);
    }
  });

  it("honors reduced-motion preference and motion controls", () => {
    render(<GlobalLandingPage />);
    const stub = screen.getByTestId("hero-stub");
    expect(stub.getAttribute("data-motion")).toBe("full");
    fireEvent.click(screen.getByRole("button", { name: "Reduce motion" }));
    expect(stub.getAttribute("data-motion")).toBe("reduced");
    fireEvent.click(screen.getByRole("button", { name: "Pause scene" }));
    expect(stub.getAttribute("data-paused")).toBe("true");
  });

  it("starts with reduced motion when the OS prefers it", async () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query === "(prefers-reduced-motion: reduce)",
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }))
    );
    const { findByTestId } = render(<GlobalLandingPage />);
    expect((await findByTestId("hero-stub")).getAttribute("data-motion")).toBe(
      "reduced"
    );
  });

  it("uses the immutable official logo inside the 3D wrapper", () => {
    render(<GlobalLandingPage />);
    const logo = screen.getByAltText("CruiseShield AI official shield logo");
    expect(logo.getAttribute("src")).toBe(
      "/assets/cruiseshield-logo-original.png"
    );
    expect(logo.getAttribute("width")).toBe("69");
    expect(logo.getAttribute("height")).toBe("73");
    const spin = logo.parentElement;
    expect(spin?.className).toContain("landing-logo-spin");
    expect(spin?.parentElement?.className).toContain("landing-logo");
    // No SVG approximation may remain in the landing brand.
    expect(
      document.querySelector(".landing-brand svg")
    ).toBeNull();
  });

  it("makes logo and brand name one home link", () => {
    render(<GlobalLandingPage />);
    const home = screen.getByRole("link", { name: "CruiseShield AI home" });
    expect(home.getAttribute("href")).toBe("/");
    const logo = screen.getByAltText("CruiseShield AI official shield logo");
    expect(logo.closest("a")).toBe(home);
    expect(home.textContent).toContain("CruiseShield AI™");
    expect(home.textContent).toContain("The Financial Crime Immune System™");
  });

  it("keeps audio OFF by default with a working toggle", () => {
    render(<GlobalLandingPage />);
    const toggle = screen.getByRole("button", { name: /Sound:/ });
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(toggle);
    // No AudioContext in jsdom: stays OFF without crashing.
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByLabelText("Volume")).toBeTruthy();
  });
});

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LandingPage from "./page";

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

// The 3D hero mounts only in a real browser (ssr:false + WebGL); stub
// it here and prove the page wires the hero slot. Live rendering is
// covered by the browser smoke check, not jsdom.
vi.mock("../components/landing/GlobalHeroScene", () => ({
  GlobalHeroScene: () => <div data-testid="hero-stub" />,
}));

// The nav bell fetches on mount; keep page tests hermetic.
vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  listNotifications: vi
    .fn()
    .mockResolvedValue({ notifications: [], unread_count: 0 }),
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

describe("primary homepage (/)", () => {
  it("resolves to the World Atlas landing experience, not a placeholder", async () => {
    const { findByTestId } = render(<LandingPage />);
    expect(screen.getAllByText("CruiseShield AI™").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "A Safer Financial World" })
    ).toBeTruthy();
    for (const step of [
      "DETECT",
      "CONNECT",
      "INVESTIGATE",
      "EXPLAIN",
      "VERIFY",
      "SIMULATE",
      "DECIDE",
      "AUDIT",
    ]) {
      expect(screen.getByText(step)).toBeTruthy();
    }
    // next/dynamic resolves asynchronously even when mocked.
    expect(await findByTestId("hero-stub")).toBeTruthy();
    // Hero CTA + WebGL-fallback CTA both target /platform (jsdom has no WebGL).
    const ctas = screen.getAllByRole("link", { name: /Explore CruiseShield AI/ });
    expect(ctas.length).toBeGreaterThanOrEqual(1);
    for (const cta of ctas) {
      expect(cta.getAttribute("href")).toBe("/platform");
    }
  });
});

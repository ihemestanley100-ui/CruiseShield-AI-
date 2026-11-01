import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SectionNav } from "./section-nav";

const ITEMS = [
  { id: "overview-h", label: "Overview" },
  { id: "why-risk-h", label: "Why this risk?" },
  { id: "evidence-h", label: "Evidence" },
];

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("SectionNav", () => {
  it("links every section by anchor without duplicating content", () => {
    render(<SectionNav items={ITEMS} />);
    const nav = screen.getByRole("navigation", { name: "On this page" });
    const links = [...nav.querySelectorAll("a")];
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      "#overview-h",
      "#why-risk-h",
      "#evidence-h",
    ]);
    expect(links.map((a) => a.textContent)).toEqual([
      "Overview",
      "Why this risk?",
      "Evidence",
    ]);
    expect(
      nav.querySelectorAll('[aria-current="true"]').length
    ).toBe(0);
  });

  it("marks the section in view as current", () => {
    document.body.innerHTML =
      '<h1 id="overview-h">t</h1><h2 id="why-risk-h">t</h2><h2 id="evidence-h">t</h2>';
    let callback: IntersectionObserverCallback = () => {};
    vi.stubGlobal(
      "IntersectionObserver",
      vi.fn().mockImplementation((cb: IntersectionObserverCallback) => {
        callback = cb;
        return { observe: vi.fn(), disconnect: vi.fn() };
      })
    );
    render(<SectionNav items={ITEMS} />);
    const target = document.getElementById("evidence-h") as Element;
    act(() => {
      callback(
        [{ target, isIntersecting: true } as IntersectionObserverEntry],
        {} as IntersectionObserver
      );
    });
    const current = screen.getByRole("link", { name: "Evidence" });
    expect(current.getAttribute("aria-current")).toBe("true");
    expect(current.className).toContain("active");
    document.body.innerHTML = "";
  });

  it("renders working links when IntersectionObserver is unavailable", () => {
    vi.stubGlobal("IntersectionObserver", undefined);
    render(<SectionNav items={ITEMS} />);
    expect(
      screen.getByRole("link", { name: "Overview" }).getAttribute("href")
    ).toBe("#overview-h");
  });
});

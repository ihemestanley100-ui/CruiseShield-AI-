import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IntelligenceFrameworkPanel } from "./IntelligenceFrameworkPanel";

describe("IntelligenceFrameworkPanel", () => {
  it("renders the exact approved framework copy", () => {
    render(<IntelligenceFrameworkPanel />);
    expect(
      screen.getByRole("heading", {
        name: "The Global Signal-to-Evidence Engine™",
      })
    ).toBeTruthy();
    expect(
      screen.getByText("Cruiseshield Intelligence Framework")
    ).toBeTruthy();
    expect(
      screen.getByText("From Disconnected Signals to Defensible Intelligence")
    ).toBeTruthy();
    expect(
      screen.getByText(
        "Connect transaction patterns, entity relationships, risk intelligence and investigation evidence through one explainable intelligence framework, with human investigators retaining decision authority."
      )
    ).toBeTruthy();
    expect(
      screen.getByText("One intelligence framework. A stronger financial world.")
    ).toBeTruthy();
  });

  it("renders eyebrow and statement as uppercase display text", () => {
    // Copy is stored in sentence case; display uppercase comes from CSS.
    const css = readFileSync(
      join(process.cwd(), "styles", "framework-panel.css"),
      "utf-8"
    );
    const eyebrow = css.match(/\.fw-eyebrow\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(eyebrow).toContain("text-transform: uppercase");
    const statement = css.match(/\.fw-statement\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(statement).toContain("text-transform: uppercase");
  });

  it("contains no hackathon references, links, or award claims", () => {
    render(<IntelligenceFrameworkPanel />);
    const panel = document.querySelector(".fw-panel") as HTMLElement;
    expect(panel).not.toBeNull();
    const text = panel.textContent ?? "";
    expect(text).not.toMatch(
      /hackathon|meta global|participant|trophy|source code|october 2026|github/i
    );
    expect(text).not.toMatch(/winner|won|award|prize|champion/i);
    expect(panel.querySelector("a")).toBeNull();
  });

  it("keeps decorative icons out of the accessibility tree", () => {
    render(<IntelligenceFrameworkPanel />);
    const panel = document.querySelector(".fw-panel") as HTMLElement;
    const svgs = panel.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThan(0);
    for (const svg of svgs) {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
    }
  });
});

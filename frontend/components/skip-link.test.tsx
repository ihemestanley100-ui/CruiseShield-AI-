import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SkipLink } from "./skip-link";

describe("SkipLink", () => {
  it("links to the main content landmark", () => {
    render(
      <>
        <SkipLink />
        <main id="main-content" tabIndex={-1}>
          <p>content</p>
        </main>
      </>
    );
    const link = screen.getByRole("link", { name: "Skip to main content" });
    expect(link.getAttribute("href")).toBe("#main-content");
    expect(link.className).toContain("skip-link");
  });
});

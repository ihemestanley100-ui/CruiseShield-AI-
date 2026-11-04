import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  HACKATHON_REPO_URL,
  HackathonRecognitionPanel,
} from "./HackathonRecognitionPanel";

describe("HackathonRecognitionPanel", () => {
  it("renders the participation plaque without award claims", () => {
    render(<HackathonRecognitionPanel />);
    expect(
      screen.getByRole("heading", {
        name: "Built at the Meta Global AI Developer Hackathon",
      })
    ).toBeTruthy();
    expect(screen.getByText("Meta Hackathon Recognition")).toBeTruthy();
    expect(screen.getByText("October 2026")).toBeTruthy();
    expect(screen.getByText("Participant")).toBeTruthy();
    // No award language anywhere in the panel.
    const text = document.querySelector(".hack-panel")?.textContent ?? "";
    expect(text).not.toMatch(/winner|won|award|prize|champion/i);
  });

  it("links the whole source row to the verified public repository", () => {
    render(<HackathonRecognitionPanel />);
    expect(HACKATHON_REPO_URL).toBe(
      "https://github.com/ihemestanley100-ui/CRUISESHIELD-AI-"
    );
    const link = screen.getByRole("link", {
      name: /Source code.*GitHub repository.*new tab/,
    });
    expect(link.getAttribute("href")).toBe(HACKATHON_REPO_URL);
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
    expect(link.getAttribute("rel")).toContain("noreferrer");
    expect(link.textContent).toContain("Source code");
  });

  it("keeps decorative icons out of the accessibility tree", () => {
    render(<HackathonRecognitionPanel />);
    const panel = document.querySelector(".hack-panel") as HTMLElement;
    const svgs = panel.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThan(0);
    for (const svg of svgs) {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
    }
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import HelpPage from "./help/page";
import LegalPage from "./legal/page";
import PrivacyPage from "./privacy/page";
import SupportPage from "./support/page";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

const PAGES: Array<[string, () => React.JSX.Element, string]> = [
  ["/help", HelpPage, "Help"],
  ["/support", SupportPage, "Support"],
  ["/legal", LegalPage, "Legal"],
  ["/privacy", PrivacyPage, "Privacy"],
];

describe.each(PAGES)("static page %s", (_route, Page, title) => {
  it("renders its title and cross-links without invented claims", () => {
    render(<Page />);
    expect(
      screen.getByRole("heading", { name: title })
    ).toBeInTheDocument();
    for (const target of ["/help", "/support", "/legal", "/privacy"]) {
      expect(
        screen.getByRole("link", { name: (_, el) => el.getAttribute("href") === target })
      ).toBeInTheDocument();
    }
    expect(document.body.textContent ?? "").not.toMatch(
      /SLA|24\/7|helpdesk|support@|guarantee/i
    );
  });
});

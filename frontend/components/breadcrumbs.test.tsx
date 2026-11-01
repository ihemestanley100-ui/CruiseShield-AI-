import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Breadcrumbs } from "./breadcrumbs";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

describe("Breadcrumbs", () => {
  it("links ancestors and marks the current page", () => {
    render(
      <Breadcrumbs
        items={[
          { label: "Command Center", href: "/" },
          { label: "Investigation inv_84721" },
        ]}
      />
    );
    const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(nav).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Command Center" }).getAttribute("href")
    ).toBe("/");
    expect(screen.getByText("Investigation inv_84721").getAttribute("aria-current")).toBe(
      "page"
    );
  });
});

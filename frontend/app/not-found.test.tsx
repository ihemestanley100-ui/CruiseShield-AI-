import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NotFound from "./not-found";

describe("branded 404", () => {
  it("links to the demo and the start page", () => {
    render(<NotFound />);
    const demo = screen.getByText("Open the demo").closest("a");
    const home = screen.getByText("Back to start").closest("a");
    expect(demo?.getAttribute("href")).toBe("/demo");
    expect(home?.getAttribute("href")).toBe("/");
  });
});

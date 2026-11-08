import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NotFound from "./not-found";

describe("branded 404", () => {
  it("links to the platform and the start page", () => {
    render(<NotFound />);
    const platform = screen.getByText("Open the platform").closest("a");
    const home = screen.getByText("Back to start").closest("a");
    expect(platform?.getAttribute("href")).toBe("/platform");
    expect(home?.getAttribute("href")).toBe("/");
  });
});

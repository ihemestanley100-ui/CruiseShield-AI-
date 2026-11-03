import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Loading from "./loading";

describe("route loading state", () => {
  it("announces loading without fake progress", () => {
    render(<Loading />);
    const region = screen.getByText("Fetching the latest demo state.");
    expect(region.closest("[aria-busy='true']")).toBeTruthy();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Stat } from "./stat";

describe("Stat", () => {
  it("announces numeric values with their label", () => {
    render(<Stat label="evidence records" value={39} caption="pkg_1" />);
    expect(screen.getByLabelText("39 evidence records")).toBeTruthy();
    expect(screen.getByText("pkg_1")).toBeTruthy();
  });

  it("renders text values such as Not available as-is", () => {
    render(<Stat label="pending decisions" value="Not available" />);
    expect(screen.getByText("Not available")).toBeTruthy();
  });
});

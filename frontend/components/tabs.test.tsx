import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Tabs } from "./tabs";

const TABS = [
  { id: "risk", label: "Risk", content: <p>Risk panel</p> },
  { id: "evidence", label: "Evidence", content: <p>Evidence panel</p> },
];

describe("Tabs", () => {
  it("shows the first panel and switches on click", () => {
    render(<Tabs tabs={TABS} label="Investigation sections" />);
    expect(screen.getByText("Risk panel")).toBeTruthy();
    expect(screen.queryByText("Evidence panel")).toBeNull();
    fireEvent.click(screen.getByRole("tab", { name: "Evidence" }));
    expect(screen.getByText("Evidence panel")).toBeTruthy();
    expect(screen.queryByText("Risk panel")).toBeNull();
    expect(
      screen.getByRole("tab", { name: "Evidence" }).getAttribute("aria-selected")
    ).toBe("true");
  });

  it("moves with arrow keys", () => {
    render(<Tabs tabs={TABS} label="Investigation sections" />);
    const list = screen.getByRole("tablist");
    fireEvent.keyDown(list, { key: "ArrowRight" });
    expect(screen.getByText("Evidence panel")).toBeTruthy();
    fireEvent.keyDown(list, { key: "ArrowLeft" });
    expect(screen.getByText("Risk panel")).toBeTruthy();
  });
});

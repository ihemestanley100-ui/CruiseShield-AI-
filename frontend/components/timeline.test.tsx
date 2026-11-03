import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Timeline } from "./timeline";

describe("Timeline", () => {
  it("renders items in the given order", () => {
    render(
      <Timeline
        items={[
          { id: "a", time: "10:00", title: "First", detail: "d1" },
          { id: "b", time: "10:05", title: "Second" },
        ]}
      />
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toContain("First");
    expect(items[1].textContent).toContain("Second");
  });

  it("shows an honest empty state", () => {
    render(<Timeline items={[]} />);
    expect(screen.getByText("No events.")).toBeTruthy();
  });

  it("localizes ISO timestamps, keeps display strings verbatim", () => {
    render(
      <Timeline
        items={[
          { id: "a", time: "2026-10-29T20:32:15Z", title: "Iso" },
          { id: "b", time: "10:00", title: "Verbatim" },
        ]}
      />
    );
    const items = screen.getAllByRole("listitem");
    expect(items[0].textContent).toContain("2026");
    expect(items[0].textContent).not.toContain("T20:32:15Z");
    expect(items[1].textContent).toContain("10:00");
  });
});

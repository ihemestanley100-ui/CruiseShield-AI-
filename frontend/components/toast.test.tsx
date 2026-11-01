import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ToastRegion } from "./toast";

describe("ToastRegion", () => {
  it("renders successes as status and errors as alerts", () => {
    render(
      <ToastRegion
        messages={[
          { id: "a", text: "Decision recorded.", tone: "ok" },
          { id: "b", text: "Simulation failed.", tone: "error" },
        ]}
      />
    );
    expect(screen.getByRole("status").textContent).toContain(
      "Decision recorded."
    );
    expect(screen.getByRole("alert").textContent).toContain(
      "Simulation failed."
    );
  });

  it("renders an empty live region with no messages", () => {
    const { container } = render(<ToastRegion messages={[]} />);
    expect(container.querySelector(".toast-region")).toBeTruthy();
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

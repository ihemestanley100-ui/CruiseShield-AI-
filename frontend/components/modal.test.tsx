import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Modal } from "./modal";

describe("Modal", () => {
  it("labels the dialog and closes on Escape or button", () => {
    const onClose = vi.fn();
    render(
      <Modal title="Confirm reset" onClose={onClose}>
        <p>Body text.</p>
      </Modal>
    );
    expect(screen.getByRole("dialog", { name: "Confirm reset" })).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Close dialog" }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("returns focus to the opener and unlocks scroll on unmount", () => {
    const onClose = vi.fn();
    render(<button type="button">Opener</button>);
    const opener = screen.getByRole("button", { name: "Opener" });
    opener.focus();
    const { unmount } = render(
      <Modal title="T" onClose={onClose}>
        <p>x</p>
      </Modal>
    );
    expect(document.body.style.overflow).toBe("hidden");
    unmount();
    expect(document.body.style.overflow).toBe("");
    expect(document.activeElement).toBe(opener);
  });
});

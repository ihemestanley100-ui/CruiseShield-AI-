import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { STORAGE_KEY } from "../lib/theme";
import { ThemeProvider } from "./theme-provider";
import { ThemeSelector } from "./theme-selector";

type ChangeListener = (event: { matches: boolean }) => void;

function mockMatchMedia(initialLight: boolean) {
  const listeners = new Set<ChangeListener>();
  const query = {
    matches: initialLight,
    media: "(prefers-color-scheme: light)",
    addEventListener: vi.fn((_type: string, cb: ChangeListener) => {
      listeners.add(cb);
    }),
    removeEventListener: vi.fn((_type: string, cb: ChangeListener) => {
      listeners.delete(cb);
    }),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: () => query,
  });
  return {
    setLight(next: boolean) {
      query.matches = next;
      listeners.forEach((cb) => cb({ matches: next }));
    },
  };
}

function checked(value: string): boolean {
  return (screen.getByRole("radio", { name: value }) as HTMLInputElement)
    .checked;
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

describe("ThemeProvider", () => {
  it("applies the system theme by default", () => {
    mockMatchMedia(false);
    render(
      <ThemeProvider>
        <p>child</p>
      </ThemeProvider>
    );
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("switches immediately and persists the choice", () => {
    mockMatchMedia(false);
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    fireEvent.click(screen.getByRole("radio", { name: "Light" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("light");
  });

  it("restores the stored theme on mount", () => {
    mockMatchMedia(false);
    localStorage.setItem(STORAGE_KEY, "dark");
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(checked("Dark")).toBe(true);
  });

  it("follows system changes in system mode", () => {
    const media = mockMatchMedia(false);
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    expect(document.documentElement.dataset.theme).toBe("dark");
    media.setLight(true);
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("exposes three labelled radio options", () => {
    mockMatchMedia(true);
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    const radios = screen.getAllByRole("radio");
    expect(
      radios.map((radio) => (radio as HTMLInputElement).value)
    ).toEqual(["dark", "light", "system"]);
    expect(
      screen.getByRole("radiogroup", { name: "Appearance" })
    ).toBeTruthy();
  });
});

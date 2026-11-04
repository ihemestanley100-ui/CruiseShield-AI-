import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LOCALE_STORAGE_KEY, LocaleProvider } from "../lib/i18n/context";
import { LanguageSelector } from "./language-selector";

function open(name: RegExp = /Select language/) {
  render(
    <LocaleProvider>
      <LanguageSelector />
    </LocaleProvider>
  );
  const button = screen.getByRole("button", { name });
  fireEvent.click(button);
  return button;
}

afterEach(() => {
  window.localStorage.clear();
  document.documentElement.lang = "en";
  document.documentElement.dir = "ltr";
});

describe("LanguageSelector", () => {
  it("shows the reference design: globe, native name, chevron", () => {
    render(
      <LocaleProvider>
        <LanguageSelector />
      </LocaleProvider>
    );
    const button = screen.getByRole("button", { name: "Select language: English" });
    expect(button.className).toContain("lang-button");
    expect(within(button).getByText("English")).toBeTruthy();
    // Globe + chevron SVGs are present but hidden from assistive tech.
    const svgs = button.querySelectorAll("svg[aria-hidden='true']");
    expect(svgs.length).toBe(2);
    expect(button.getAttribute("aria-haspopup")).toBe("listbox");
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });

  it("opens a searchable native-script panel and filters on input", () => {
    open();
    const search = screen.getByRole("combobox");
    expect(search.getAttribute("placeholder")).toBe("Search languages…");
    fireEvent.change(search, { target: { value: "العربية" } });
    const listbox = screen.getByRole("listbox");
    const options = within(listbox).getAllByRole("option");
    // Only ar: ar-EG/ar-SA have no dictionary and stay hidden.
    expect(options.length).toBe(1);
    for (const option of options) {
      expect(option.textContent).toContain("العربية");
    }
    fireEvent.change(search, { target: { value: "zzz-no-such" } });
    expect(screen.getByText("No languages match your search.")).toBeTruthy();
  });

  it("selects with mouse/touch click and persists the preference", () => {
    open();
    const search = screen.getByRole("combobox");
    fireEvent.change(search, { target: { value: "français" } });
    const option = screen.getByRole("option", { name: /français/ });
    fireEvent.click(option);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("fr");
    expect(document.documentElement.lang).toBe("fr");
    expect(screen.getByRole("button", { name: /français/ })).toBeTruthy();
  });

  it("navigates with ArrowDown/Home/End and chooses with Enter", () => {
    open();
    const search = screen.getByRole("combobox");
    fireEvent.keyDown(search, { key: "End" });
    fireEvent.keyDown(search, { key: "Home" });
    fireEvent.keyDown(search, { key: "ArrowDown" });
    fireEvent.keyDown(search, { key: "Enter" });
    // Dictionaries only: first entry ar, second en.
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en");
  });

  it("closes on Escape and returns focus to the button", () => {
    const button = open();
    expect(screen.getByRole("listbox")).toBeTruthy();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("hides entries without translations and never badges fallback", () => {
    open();
    const search = screen.getByRole("combobox");
    // isiZulu (zu) has no dictionary: hidden from the list entirely.
    fireEvent.change(search, { target: { value: "isiZulu" } });
    expect(
      screen.getByText("No languages match your search.")
    ).toBeTruthy();
    fireEvent.change(search, { target: { value: "" } });
    expect(
      screen.queryByText("English fallback")
    ).toBeNull();
  });

  it("keeps the explicit note for legacy persisted unavailable locales", () => {
    // Users who picked an unavailable locale before it was hidden
    // still get English plus the explicit fallback note.
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "zu");
    render(
      <LocaleProvider>
        <LanguageSelector />
      </LocaleProvider>
    );
    const button = screen.getByRole("button", { name: /isiZulu/ });
    fireEvent.click(button);
    expect(
      screen.getByText("English shown — translation unavailable")
    ).toBeTruthy();
  });

  it("badges partial locales without the unavailable warning", () => {
    open();
    const search = screen.getByRole("combobox");
    fireEvent.change(search, { target: { value: "Yorùbá" } });
    const option = screen.getByRole("option", { name: /Yorùbá/ });
    expect(option.textContent).toContain("Partial");
    fireEvent.click(option);
    fireEvent.click(screen.getByRole("button", { name: /Yorùbá/ }));
    expect(
      screen.queryByText("English shown — translation unavailable")
    ).toBeNull();
  });

  it("isolates non-Latin endonyms for bidirectional text", () => {
    open();
    const search = screen.getByRole("combobox");
    // Arabic (RTL) and Japanese (CJK) render in their own scripts,
    // isolated so they cannot reorder the surrounding row text.
    fireEvent.change(search, { target: { value: "العربية" } });
    const arabic = screen.getByRole("option", { name: /العربية/ });
    const arabicNative = within(arabic).getByText("العربية");
    expect(arabicNative.tagName).toBe("BDI");
    expect(arabicNative.getAttribute("lang")).toBe("ar");
    fireEvent.change(search, { target: { value: "日本語" } });
    const japanese = screen.getByRole("option", { name: /日本語/ });
    const japaneseNative = within(japanese).getByText("日本語");
    expect(japaneseNative.tagName).toBe("BDI");
    expect(japaneseNative.getAttribute("lang")).toBe("ja");
  });

  it("marks the current option selected for screen readers", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    open(/Choisir la langue/);
    const search = screen.getByRole("combobox");
    fireEvent.change(search, { target: { value: "français" } });
    const options = screen.getAllByRole("option", { name: /français/ });
    const selected = options.filter(
      (option) => option.getAttribute("aria-selected") === "true"
    );
    expect(selected).toHaveLength(1);
    expect(selected[0]?.textContent).toContain("français");
  });
});

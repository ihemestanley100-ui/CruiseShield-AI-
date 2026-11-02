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
    // ar plus its ar-EG and ar-SA regional variants.
    expect(options.length).toBe(3);
    for (const option of options) {
      expect(option.textContent).toContain("العربية");
    }
    fireEvent.change(search, { target: { value: "zzz-no-such" } });
    expect(screen.getByText("No languages match your search.")).toBeTruthy();
  });

  it("selects with mouse/touch click and persists the preference", () => {
    open();
    const search = screen.getByRole("combobox");
    fireEvent.change(search, { target: { value: "français (Canada)" } });
    const option = screen.getByRole("option", { name: /français/ });
    fireEvent.click(option);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("fr-CA");
    expect(document.documentElement.lang).toBe("fr-CA");
    expect(screen.getByRole("button", { name: /français/ })).toBeTruthy();
  });

  it("navigates with ArrowDown/Home/End and chooses with Enter", () => {
    open();
    const search = screen.getByRole("combobox");
    fireEvent.keyDown(search, { key: "End" });
    fireEvent.keyDown(search, { key: "Home" });
    fireEvent.keyDown(search, { key: "ArrowDown" });
    fireEvent.keyDown(search, { key: "Enter" });
    // First entry is Afar (aa), second Abkhaz (ab).
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("ab");
  });

  it("closes on Escape and returns focus to the button", () => {
    const button = open();
    expect(screen.getByRole("listbox")).toBeTruthy();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("badges translation status and warns on English fallback", () => {
    open();
    const search = screen.getByRole("combobox");
    // isiZulu (zu) has no dictionary: the honest unavailable example.
    fireEvent.change(search, { target: { value: "isiZulu" } });
    const option = screen.getByRole("option", { name: /isiZulu/ });
    expect(option.textContent).toContain("English fallback");
    fireEvent.click(option);
    // Unavailable locale: UI stays English with an explicit note on reopen.
    expect(screen.getByRole("button", { name: /isiZulu/ })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /isiZulu/ }));
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

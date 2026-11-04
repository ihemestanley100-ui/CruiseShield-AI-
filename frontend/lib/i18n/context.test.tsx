import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  LOCALE_STORAGE_KEY,
  LocaleProvider,
  applyDocumentLocale,
  detectLocale,
  readStoredLocale,
  useLocale,
  useTranslation,
} from "./context";

function Probe() {
  const { locale, dir, setLocale } = useLocale();
  const { t } = useTranslation("nav");
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="dir">{dir}</span>
      <span data-testid="text">{t("commandCenter")}</span>
      <button type="button" onClick={() => setLocale("ar")}>
        to-ar
      </button>
      <button type="button" onClick={() => setLocale("xx")}>
        to-invalid
      </button>
    </div>
  );
}

function mockLanguages(languages: string[]) {
  Object.defineProperty(window.navigator, "languages", {
    value: languages,
    configurable: true,
  });
}

afterEach(() => {
  window.localStorage.clear();
  document.documentElement.lang = "en";
  document.documentElement.dir = "ltr";
  Object.defineProperty(window.navigator, "languages", {
    value: ["en"],
    configurable: true,
  });
  vi.unstubAllGlobals();
});

describe("locale context", () => {
  it("translates to English without a provider (existing-test safe)", () => {
    function Bare() {
      const { t } = useTranslation("auth");
      return <span>{t("signIn")}</span>;
    }
    render(<Bare />);
    expect(screen.getByText("Sign in")).toBeTruthy();
  });

  it("reads a stored preference, ignoring unknown tags", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    expect(readStoredLocale()).toBe("fr");
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "xx");
    expect(readStoredLocale()).toBeNull();
  });

  it("detects the browser locale list", () => {
    expect(detectLocale(["fr-CA", "en"])).toBe("fr-CA");
    expect(detectLocale(["xx"])).toBe("en");
    expect(detectLocale([])).toBe("en");
  });

  it("prefers the stored choice over browser detection", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "ar");
    mockLanguages(["fr"]);
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>
    );
    expect(screen.getByTestId("locale").textContent).toBe("ar");
    expect(screen.getByTestId("text").textContent).toBe("مركز القيادة");
  });

  it("first render matches SSR fallback with a stored locale", () => {
    // SSR always paints FALLBACK_LOCALE; the first client render must
    // agree or React throws #418 on every returning visit (observed in
    // armed Edge QA). The stored choice applies in the mount effect.
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "ar");
    mockLanguages(["en"]);
    const seen: string[] = [];
    function Recorder() {
      const { locale } = useLocale();
      seen.push(locale);
      return null;
    }
    render(
      <LocaleProvider>
        <Recorder />
      </LocaleProvider>
    );
    expect(seen[0]).toBe("en");
    expect(seen[seen.length - 1]).toBe("ar");
  });

  it("falls back to detection when nothing is stored", () => {
    mockLanguages(["fr"]);
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>
    );
    expect(screen.getByTestId("locale").textContent).toBe("fr");
    expect(screen.getByTestId("text").textContent).toBe("Centre de commandement");
  });

  it("persists the choice, syncs lang/dir, and survives remount", () => {
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>
    );
    fireEvent.click(screen.getByText("to-ar"));
    expect(screen.getByTestId("locale").textContent).toBe("ar");
    expect(screen.getByTestId("dir").textContent).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");
    expect(document.documentElement.dir).toBe("rtl");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("ar");
  });

  it("ignores unknown tags without changing state", () => {
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>
    );
    fireEvent.click(screen.getByText("to-invalid"));
    expect(screen.getByTestId("locale").textContent).toBe("en");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBeNull();
  });

  it("applies document lang/dir directly, including RTL", () => {
    applyDocumentLocale("he");
    expect(document.documentElement.lang).toBe("he");
    expect(document.documentElement.dir).toBe("rtl");
    applyDocumentLocale("en");
    expect(document.documentElement.dir).toBe("ltr");
  });
});

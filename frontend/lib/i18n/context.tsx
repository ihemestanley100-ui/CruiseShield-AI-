"use client";

/* Locale provider: persisted preference, browser detection with
 * explicit override, document lang/dir sync. Works without a
 * provider (default context = English), so existing tests that
 * render components directly see byte-identical text. */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  FALLBACK_LOCALE,
  lookup,
  lookupForms,
  lookupList,
  selectPlural,
} from "./dictionaries";
import {
  LOCALE_STORAGE_KEY,
  getLanguage,
  isRtl,
  matchBrowserLocales,
} from "./registry";

export { LOCALE_STORAGE_KEY };

export function readStoredLocale(): string | null {
  try {
    const value = localStorage.getItem(LOCALE_STORAGE_KEY);
    return value !== null && getLanguage(value) !== undefined ? value : null;
  } catch {
    return null;
  }
}

export function detectLocale(
  languages: readonly string[] = typeof navigator === "undefined"
    ? []
    : [...navigator.languages]
): string {
  if (languages.length === 0) return FALLBACK_LOCALE;
  return matchBrowserLocales(languages, FALLBACK_LOCALE);
}

/* Explicit `?locale=` URL override (testing, shared links).
 * Returns the tag only when it names a registered language. */
export function urlLocaleOverride(
  search: string = typeof window === "undefined" ? "" : window.location.search
): string | null {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const tag = params.get("locale");
  if (tag === null || getLanguage(tag) === undefined) return null;
  return tag;
}

export function applyDocumentLocale(tag: string): void {
  if (typeof document === "undefined") return;
  document.documentElement.lang = tag;
  document.documentElement.dir = isRtl(tag) ? "rtl" : "ltr";
}

interface LocaleContextValue {
  locale: string;
  setLocale: (tag: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  dir: "rtl" | "ltr";
}

function defaultTranslate(
  key: string,
  vars?: Record<string, string | number>
): string {
  return lookup(FALLBACK_LOCALE, key, vars).text;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: FALLBACK_LOCALE,
  setLocale: () => {},
  t: defaultTranslate,
  dir: "ltr",
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  /* SSR-safe initial state: the server cannot know the visitor's stored
   * choice, so the first render always uses the fallback. Reading
   * storage here mismatches SSR text on every returning visit (React
   * #418). The layout effect below applies the real locale before
   * paint, so there is no fallback frame either. */
  const [locale, setLocaleState] = useState<string>(FALLBACK_LOCALE);

  /* Initial locale, once: an explicit `?locale=` override wins and
   * is persisted; else the stored choice; else browser detection.
   * Layout effect (not passive): runs before paint, so the first
   * painted frame already shows the resolved locale. Dev-only cost:
   * React logs a useLayoutEffect-does-nothing-on-the-server warning
   * during SSR; production output is unaffected. */
  useLayoutEffect(() => {
    const override = urlLocaleOverride();
    if (override !== null) {
      try {
        localStorage.setItem(LOCALE_STORAGE_KEY, override);
      } catch {
        /* private mode: applies for this session only */
      }
      setLocaleState(override);
      return;
    }
    const stored = readStoredLocale();
    if (stored !== null) {
      setLocaleState(stored);
      return;
    }
    const detected = detectLocale();
    if (detected !== FALLBACK_LOCALE) setLocaleState(detected);
  }, []);

  useEffect(() => {
    applyDocumentLocale(locale);
  }, [locale]);

  const setLocale = useCallback((tag: string) => {
    if (getLanguage(tag) === undefined) return;
    try {
      localStorage.setItem(LOCALE_STORAGE_KEY, tag);
    } catch {
      /* private mode: preference simply does not persist */
    }
    setLocaleState(tag);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      lookup(locale, key, vars).text,
    [locale]
  );

  const value = useMemo(
    () => ({ locale, setLocale, t, dir: isRtl(locale) ? ("rtl" as const) : ("ltr" as const) }),
    [locale, setLocale, t]
  );

  return (
    <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  return useContext(LocaleContext);
}

/* Namespace-bound translator: const { t, tl, tp } = useTranslation("nav").
 * `tl` resolves translated string lists (journeys, regions, ...);
 * `tp` resolves plural-form maps with Intl.PluralRules selection. */
export function useTranslation(namespace: string): {
  t: (key: string, vars?: Record<string, string | number>) => string;
  tl: (key: string) => string[];
  tp: (
    key: string,
    count: number,
    vars?: Record<string, string | number>
  ) => string;
  locale: string;
} {
  const { locale, t: root } = useLocale();
  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      root(`${namespace}.${key}`, vars),
    [root, namespace]
  );
  const tl = useCallback(
    (key: string) => lookupList(locale, `${namespace}.${key}`),
    [locale, namespace]
  );
  const tp = useCallback(
    (key: string, count: number, vars?: Record<string, string | number>) => {
      const forms = lookupForms(locale, `${namespace}.${key}`);
      const template = selectPlural(locale, count, forms);
      if (vars === undefined) return template;
      return template.replace(/\{(\w+)\}/g, (match, name: string) =>
        vars[name] === undefined ? match : String(vars[name])
      );
    },
    [locale, namespace]
  );
  return { t, tl, tp, locale };
}

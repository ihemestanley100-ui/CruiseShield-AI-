"use client";

/* Universal Global Language Selector: globe icon, native language
 * name, dropdown arrow, rounded orange border (reference design).
 * Searchable listbox panel: full keyboard navigation (arrows/Home/
 * End/Enter/Escape/type-to-filter), screen-reader labelled, and
 * touch-friendly targets. Unavailable languages stay selectable but
 * are badged with the English-fallback status — never silent. */

import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  LANGUAGES,
  getLanguage,
} from "../lib/i18n/registry";
import { useLocale, useTranslation } from "../lib/i18n/context";

function GlobeIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      aria-hidden="true"
      className="lang-globe"
    >
      <circle
        cx="9"
        cy="9"
        r="7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M2 9h14M9 2c2.4 2.1 3.6 4.4 3.6 7S11.4 13.9 9 16c-2.4-2.1-3.6-4.4-3.6-7S6.6 4.1 9 2z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
      />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      aria-hidden="true"
      className={open ? "lang-chevron open" : "lang-chevron"}
    >
      <path
        d="M3 5.5L7 9.5L11 5.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function LanguageSelector({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale } = useLocale();
  const { t } = useTranslation("selector");
  const current = getLanguage(locale);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);
  const listId = useId();
  const searchId = useId();

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (needle === "") return LANGUAGES;
    return LANGUAGES.filter(
      (entry) =>
        entry.native.toLowerCase().includes(needle) ||
        entry.english.toLowerCase().includes(needle) ||
        entry.tag.toLowerCase().includes(needle) ||
        entry.iso.toLowerCase() === needle
    );
  }, [query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    if (open) searchRef.current?.focus();
  }, [open ]);

  /* Close on outside pointer-down or Escape; focus returns to the
   * button so keyboard and screen-reader users keep context. */
  useEffect(() => {
    if (!open) return;
    function onPointer(ev: PointerEvent) {
      if (
        ev.target instanceof Node &&
        (buttonRef.current?.contains(ev.target) ||
          document.getElementById(listId)?.parentElement?.contains(ev.target))
      ) {
        return;
      }
      setOpen(false);
    }
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, listId]);

  function choose(tag: string) {
    setLocale(tag);
    setOpen(false);
    setQuery("");
    buttonRef.current?.focus();
  }

  function onSearchKey(ev: React.KeyboardEvent) {
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (ev.key === "Home") {
      ev.preventDefault();
      setActiveIndex(0);
    } else if (ev.key === "End") {
      ev.preventDefault();
      setActiveIndex(Math.max(results.length - 1, 0));
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      const entry = results[activeIndex];
      if (entry !== undefined) choose(entry.tag);
    }
  }

  const statusTag =
    current?.status === "translated"
      ? t("translatedTag")
      : current?.status === "partial"
        ? t("partialTag")
        : t("unavailableTag");

  return (
    <div className={compact ? "lang-selector compact" : "lang-selector"}>
      <button
        ref={buttonRef}
        type="button"
        className="lang-button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={`${t("buttonLabel")}: ${current?.native ?? locale}`}
        onClick={() => setOpen((v) => !v)}
      >
        <GlobeIcon />
        <span className="lang-current" lang={current?.tag}>
          {current?.native ?? locale}
        </span>
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="lang-panel" role="dialog" aria-label={t("panelTitle")}>
          <label className="visually-hidden" htmlFor={searchId}>
            {t("searchLabel")}
          </label>
          <input
            ref={searchRef}
            id={searchId}
            type="search"
            className="text-input lang-search"
            placeholder={t("searchPlaceholder")}
            value={query}
            onChange={(ev) => setQuery(ev.target.value)}
            onKeyDown={onSearchKey}
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={
              results[activeIndex] !== undefined
                ? `${listId}-opt-${activeIndex}`
                : undefined
            }
            autoComplete="off"
          />
          {results.length === 0 ? (
            <p className="muted lang-empty" role="status">
              {t("resultsEmpty")}
            </p>
          ) : (
            <ul
              id={listId}
              role="listbox"
              aria-label={t("panelTitle")}
              className="lang-list"
            >
              {results.map((entry, index) => (
                <li
                  key={entry.tag}
                  id={`${listId}-opt-${index}`}
                  role="option"
                  aria-selected={entry.tag === locale}
                  data-active={index === activeIndex || undefined}
                  onClick={() => choose(entry.tag)}
                  onMouseEnter={() => setActiveIndex(index)}
                  className="lang-option"
                >
                  <span className="lang-option-native" lang={entry.tag}>
                    {entry.native}
                  </span>
                  <span className="muted lang-option-meta">
                    {entry.english} · {entry.tag}
                  </span>
                  <span
                    className={`lang-status lang-status-${entry.status}`}
                  >
                    {entry.status === "translated"
                      ? t("translatedTag")
                      : entry.status === "partial"
                        ? t("partialTag")
                        : t("unavailableTag")}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {current?.status === "unavailable" && (
            <p className="muted lang-fallback-note" role="note">
              {t("fallbackNote")}
            </p>
          )}
        </div>
      )}
      <span className="visually-hidden" role="status">
        {t("label")}: {current?.native} ({statusTag})
      </span>
    </div>
  );
}

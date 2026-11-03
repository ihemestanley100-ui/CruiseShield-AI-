"use client";

import { useTranslation } from "../lib/i18n/context";

/* Skip link: first tab stop on every page, jumping past the header
 * and navigation straight to the main content landmark. Visually
 * hidden until focused (see .skip-link). Target: #main-content. */
export function SkipLink() {
  const { t } = useTranslation("nav");
  return (
    <a href="#main-content" className="skip-link">
      {t("skipToContent")}
    </a>
  );
}

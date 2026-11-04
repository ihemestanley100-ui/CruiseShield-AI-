"use client";

import type { ThemeMode } from "../lib/theme";
import { useTranslation } from "../lib/i18n/context";
import { useTheme } from "./theme-provider";

const OPTIONS: ReadonlyArray<ThemeMode> = ["dark", "light", "system"];

export function ThemeSelector() {
  const { mode, setMode } = useTheme();
  const { t } = useTranslation("theme");
  return (
    <div className="theme-selector" role="radiogroup" aria-label={t("appearance")}>
      {OPTIONS.map((value) => (
        <label key={value}>
          <input
            type="radio"
            name="cruiseshield-theme"
            value={value}
            checked={mode === value}
            onChange={() => setMode(value)}
          />
          {t(value)}
        </label>
      ))}
    </div>
  );
}

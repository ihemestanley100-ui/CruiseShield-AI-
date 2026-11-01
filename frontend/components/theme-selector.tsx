"use client";

import type { ThemeMode } from "../lib/theme";
import { useTheme } from "./theme-provider";

const OPTIONS: ReadonlyArray<{ value: ThemeMode; label: string }> = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "system", label: "System" },
];

export function ThemeSelector() {
  const { mode, setMode } = useTheme();
  return (
    <div className="theme-selector" role="radiogroup" aria-label="Appearance">
      {OPTIONS.map((option) => (
        <label key={option.value}>
          <input
            type="radio"
            name="cruiseshield-theme"
            value={option.value}
            checked={mode === option.value}
            onChange={() => setMode(option.value)}
          />
          {option.label}
        </label>
      ))}
    </div>
  );
}

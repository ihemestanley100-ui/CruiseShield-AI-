/* Theme preference model (pure logic; safe to unit-test without a DOM). */

export type ThemeMode = "dark" | "light" | "system";
export type ResolvedTheme = "dark" | "light";

export const STORAGE_KEY = "cruiseshield-theme";

/* Keep in sync with the no-flash inline script in app/layout.tsx. */
export function readStoredMode(): ThemeMode {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "dark" || value === "light" || value === "system"
      ? value
      : "system";
  } catch {
    return "system";
  }
}

export function resolveTheme(
  mode: ThemeMode,
  systemIsLight: boolean
): ResolvedTheme {
  if (mode === "dark") return "dark";
  if (mode === "light") return "light";
  return systemIsLight ? "light" : "dark";
}

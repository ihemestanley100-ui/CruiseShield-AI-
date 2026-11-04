/* Per-locale translation coverage against the English source.
 * Used by the maintained coverage test and the coverage report. */

import {
  AVAILABLE_DICTIONARIES,
  flattenKeys,
} from "./dictionaries";
import { ar } from "./locales/ar";
import { en } from "./locales/en";
import { es } from "./locales/es";
import { fr } from "./locales/fr";
import { ha } from "./locales/ha";
import { hi } from "./locales/hi";
import { ig } from "./locales/ig";
import { ja } from "./locales/ja";
import { pt } from "./locales/pt";
import { sw } from "./locales/sw";
import { yo } from "./locales/yo";
import { zh } from "./locales/zh";
import { LANGUAGES } from "./registry";

const DICTS: Record<string, unknown> = {
  en,
  fr,
  ar,
  es,
  ha,
  hi,
  ig,
  ja,
  pt,
  sw,
  yo,
  zh,
};

export interface LocaleCoverage {
  tag: string;
  keys: number;
  total: number;
  coverage: number;
  missing: string[];
}

export function englishKeyPaths(): string[] {
  return flattenKeys(
    en as unknown as Parameters<typeof flattenKeys>[0]
  ).sort();
}

export function coverageFor(tag: string): LocaleCoverage {
  const total = englishKeyPaths();
  const dict = DICTS[tag];
  if (dict === undefined) {
    return { tag, keys: 0, total: total.length, coverage: 0, missing: total };
  }
  const present = new Set(
    flattenKeys(dict as Parameters<typeof flattenKeys>[0])
  );
  const missing = total.filter((key) => !present.has(key));
  return {
    tag,
    keys: total.length - missing.length,
    total: total.length,
    coverage: total.length === 0 ? 1 : (total.length - missing.length) / total.length,
    missing,
  };
}

export interface CoverageSummary {
  totalKeys: number;
  locales: LocaleCoverage[];
  translated: number;
  partial: number;
  unavailable: number;
}

export function coverageSummary(): CoverageSummary {
  const translated = LANGUAGES.filter((l) => l.status === "translated").length;
  const partial = LANGUAGES.filter((l) => l.status === "partial").length;
  const unavailable = LANGUAGES.filter((l) => l.status === "unavailable").length;
  return {
    totalKeys: englishKeyPaths().length,
    locales: [...AVAILABLE_DICTIONARIES].map(coverageFor),
    translated,
    partial,
    unavailable,
  };
}

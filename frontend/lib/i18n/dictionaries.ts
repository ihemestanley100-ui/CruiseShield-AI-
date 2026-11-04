/* Dictionary lookup: namespaced keys, English fallback, missing-key
 * tracking, {var} interpolation, and plural selection. Data values
 * (IDs, scores, evidence, server labels) never pass through here. */

import { en } from "./locales/en";
import { ar } from "./locales/ar";
import { fr } from "./locales/fr";
import { es } from "./locales/es";
import { ha } from "./locales/ha";
import { hi } from "./locales/hi";
import { ig } from "./locales/ig";
import { ja } from "./locales/ja";
import { pt } from "./locales/pt";
import { sw } from "./locales/sw";
import { yo } from "./locales/yo";
import { zh } from "./locales/zh";
import { resolveDictionaryTag } from "./registry";

export const FALLBACK_LOCALE = "en";

export type Dictionary = { readonly [k: string]: DictNode };
export type DictNode =
  | string
  | readonly string[]
  | readonly (readonly string[])[]
  | { readonly [k: string]: DictNode };

const DICTIONARIES: Record<string, Dictionary> = {
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
export const AVAILABLE_DICTIONARIES: ReadonlySet<string> = new Set(
  Object.keys(DICTIONARIES)
);

/* Flatten a namespace tree to dotted key paths: {a:{b:["x"]}} ->
 * ["a.b.0"]. Arrays of arrays flatten two levels. */
export function flattenKeys(node: DictNode, prefix = ""): string[] {
  if (typeof node === "string") return [prefix];
  if (Array.isArray(node)) {
    return node.flatMap((child, i) =>
      flattenKeys(child as DictNode, prefix === "" ? String(i) : `${prefix}.${i}`)
    );
  }
  return Object.entries(node).flatMap(([key, child]) =>
    flattenKeys(child, prefix === "" ? key : `${prefix}.${key}`)
  );
}

function getNode(dict: DictNode, path: string[]): DictNode | undefined {
  let node: DictNode = dict;
  for (const segment of path) {
    if (typeof node === "string") return undefined;
    if (Array.isArray(node)) {
      const index = Number(segment);
      if (!Number.isInteger(index) || index < 0 || index >= node.length) {
        return undefined;
      }
      node = (node as readonly DictNode[])[index] as DictNode;
      continue;
    }
    const record = node as { readonly [k: string]: DictNode | undefined };
    const next = record[segment];
    if (next === undefined) return undefined;
    node = next;
  }
  return node;
}

function getPath(dict: DictNode, path: string[]): string | undefined {
  const node = getNode(dict, path);
  return typeof node === "string" ? node : undefined;
}

/* Missing-key ledger: populated when a key misses a locale that HAS
 * a dictionary (a translation gap) or misses even English (a product
 * bug). Whole-locale English fallback for undictionaried languages
 * is a known registry status, not a per-key gap, so it stays out of
 * the ledger; the selector badges it instead. */
const missingKeys = new Set<string>();

export function getMissingKeys(): string[] {
  return [...missingKeys].sort();
}

export function clearMissingKeys(): void {
  missingKeys.clear();
}

export function interpolate(
  template: string,
  vars?: Record<string, string | number>
): string {
  if (vars === undefined) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    vars[name] === undefined ? match : String(vars[name])
  );
}

export interface LookupResult {
  text: string;
  /** True when the requested locale lacked the key (fallback used). */
  fellBack: boolean;
}

/* Look up `namespace.key.path` for `tag` with BCP 47 fallback, then
 * English. A key missing even in English is a bug: development and
 * test builds render an explicit [key] marker so it can never pass
 * silently as correct text; production renders the key path itself
 * rather than wrong-language text. */
export function lookup(
  tag: string,
  fullKey: string,
  vars?: Record<string, string | number>
): LookupResult {
  const path = fullKey.split(".");
  const dictTag = resolveDictionaryTag(tag, AVAILABLE_DICTIONARIES, FALLBACK_LOCALE);
  const direct = getPath(DICTIONARIES[dictTag] as DictNode, path);
  if (direct !== undefined) {
    return { text: interpolate(direct, vars), fellBack: dictTag !== tag };
  }
  const english = getPath(en as unknown as DictNode, path);
  if (english !== undefined) {
    missingKeys.add(`${tag}:${fullKey}`);
    return { text: interpolate(english, vars), fellBack: true };
  }
  missingKeys.add(`en:${fullKey}`);
  const marker = `[${fullKey}]`;
  return { text: marker, fellBack: true };
}

/* List lookup for translated arrays (journeys, signals, regions):
 * whole-list fallback to English when the locale lacks the list. */
export function lookupList(tag: string, fullKey: string): string[] {
  const path = fullKey.split(".");
  const dictTag = resolveDictionaryTag(tag, AVAILABLE_DICTIONARIES, FALLBACK_LOCALE);
  const direct = getNode(DICTIONARIES[dictTag] as DictNode, path);
  if (Array.isArray(direct) && direct.every((v) => typeof v === "string")) {
    return [...(direct as string[])];
  }
  const english = getNode(en as unknown as DictNode, path);
  if (Array.isArray(english)) {
    missingKeys.add(`${tag}:${fullKey}`);
    return [...(english as string[])];
  }
  missingKeys.add(`en:${fullKey}`);
  return [];
}

/* Plural-form lookup: resolves `namespace.key` to a {category: template}
 * map (whole-map fallback to English). Used by tp(). */
export function lookupForms(
  tag: string,
  fullKey: string
): Partial<Record<Intl.LDMLPluralRule, string>> {
  const path = fullKey.split(".");
  const dictTag = resolveDictionaryTag(tag, AVAILABLE_DICTIONARIES, FALLBACK_LOCALE);
  const direct = getNode(DICTIONARIES[dictTag] as DictNode, path);
  if (direct !== undefined && typeof direct === "object" && !Array.isArray(direct)) {
    const entries = Object.entries(direct).filter(([, v]) => typeof v === "string");
    if (entries.length > 0) return Object.fromEntries(entries);
  }
  const english = getNode(en as unknown as DictNode, path);
  if (english !== undefined && typeof english === "object" && !Array.isArray(english)) {
    missingKeys.add(`${tag}:${fullKey}`);
    return Object.fromEntries(
      Object.entries(english).filter(([, v]) => typeof v === "string")
    );
  }
  missingKeys.add(`en:${fullKey}`);
  return {};
}

/* Fallback report: ledger grouped by requested locale for the
 * missing-key report and QA tooling. */
export function reportFallbacks(): Record<string, string[]> {
  const grouped: Record<string, string[]> = {};
  for (const entry of [...missingKeys].sort()) {
    const split = entry.indexOf(":");
    const tag = split < 0 ? entry : entry.slice(0, split);
    const key = split < 0 ? "" : entry.slice(split + 1);
    (grouped[tag] ??= []).push(key);
  }
  return grouped;
}

/* Plural selection via Intl.PuralRules. `forms` maps plural
 * categories to templates; missing categories fall back along
 * category -> "other" -> first available form. */
export function selectPlural(
  tag: string,
  count: number,
  forms: Partial<Record<Intl.LDMLPluralRule, string>>
): string {
  let rule: Intl.LDMLPluralRule = "other";
  try {
    rule = new Intl.PluralRules(tag).select(count);
  } catch {
    rule = new Intl.PluralRules(FALLBACK_LOCALE).select(count);
  }
  const template =
    forms[rule] ?? forms.other ?? Object.values(forms)[0] ?? "{count}";
  return interpolate(template, { count });
}

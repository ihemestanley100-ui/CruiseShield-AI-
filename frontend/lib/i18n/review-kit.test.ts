import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { englishKeyPaths } from "./coverage";
import { clearMissingKeys, lookup } from "./dictionaries";
import { getLocaleMeta } from "./meta";

/* Reviewer-readable per-locale TSV kit under docs/UGLS_REVIEW_KIT.
 * Default mode verifies the kit matches the dictionaries exactly
 * (stale kit fails: re-run with UGLS_REGEN_KIT=1 after any catalog
 * change). Regen mode rewrites the TSVs. Values use the real lookup
 * machinery, so flags below describe production behavior, not a
 * parallel implementation. */

const KIT_TAGS = [
  "fr",
  "ar",
  "ig",
  "yo",
  "ha",
  "pt",
  "es",
  "zh",
  "hi",
  "sw",
  "ja",
];

const KIT_DIR = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "..",
  "docs",
  "UGLS_REVIEW_KIT"
);

const REGEN = process.env.UGLS_REGEN_KIT === "1";

function escapeCell(value: string): string {
  return value.replace(/\t/g, " ").replace(/\r?\n/g, "\\n");
}

function varsOf(template: string): string {
  const names = [...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]);
  return [...new Set(names)].sort().join(",");
}

function buildTsv(tag: string): string {
  const meta = getLocaleMeta(tag);
  if (meta === undefined) throw new Error(`no meta for ${tag}`);
  clearMissingKeys();
  const lines = [
    `# locale: ${tag} (MACHINE-DRAFTED — human review pending)`,
    `# version: ${meta.version} | sourceRev: ${meta.sourceRev} | review: ${meta.review}`,
    "# columns: key | en_source | draft | origin(direct=translated,fallback=English shown) | same_as_source | en_vars | draft_vars | vars_ok",
    "key\ten_source\tdraft\torigin\tsame_as_source\ten_vars\tdraft_vars\tvars_ok",
  ];
  for (const key of englishKeyPaths()) {
    const en = lookup("en", key).text;
    const found = lookup(tag, key);
    const draft = found.text;
    const enVars = varsOf(en);
    const draftVars = varsOf(draft);
    lines.push(
      [
        key,
        escapeCell(en),
        escapeCell(draft),
        found.fellBack ? "fallback" : "direct",
        draft === en ? "true" : "false",
        enVars,
        draftVars,
        enVars === draftVars ? "true" : "false",
      ].join("\t")
    );
  }
  clearMissingKeys();
  return lines.join("\n") + "\n";
}

describe("translation review kit", () => {
  for (const tag of KIT_TAGS) {
    it(`kit for ${tag} matches the dictionaries`, () => {
      const tsv = buildTsv(tag);
      const file = resolve(KIT_DIR, `${tag}.tsv`);
      if (REGEN) {
        mkdirSync(KIT_DIR, { recursive: true });
        writeFileSync(file, tsv);
        return;
      }
      if (!existsSync(file)) {
        throw new Error(
          `missing kit ${tag}.tsv — regenerate with UGLS_REGEN_KIT=1`
        );
      }
      expect(readFileSync(file, "utf8")).toBe(tsv);
    });
  }
});

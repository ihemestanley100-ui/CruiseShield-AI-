/* Translation versioning + human-review tracking. Every dictionary
 * carries a version; unreviewed locales stay machine-drafted and are
 * NEVER reported as human-verified. See docs/UGLS_HUMAN_REVIEW_REGISTER.md. */

export type ReviewState = "source" | "machine-drafted" | "human-reviewed";

export interface LocaleMeta {
  tag: string;
  /** Dictionary content version (bump on any value change). */
  version: string;
  /** English source revision this translation was drafted against. */
  sourceRev: string;
  review: ReviewState;
  reviewers: string[];
  updated: string;
}

export const SOURCE_REV = "2026-11-02-ugls02";

export const LOCALE_META: Record<string, LocaleMeta> = {
  en: {
    tag: "en",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "source",
    reviewers: [],
    updated: "2026-11-02",
  },
  fr: {
    tag: "fr",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  ar: {
    tag: "ar",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  ig: {
    tag: "ig",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  yo: {
    tag: "yo",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  ha: {
    tag: "ha",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  pt: {
    tag: "pt",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  es: {
    tag: "es",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  zh: {
    tag: "zh",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  hi: {
    tag: "hi",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  sw: {
    tag: "sw",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
  ja: {
    tag: "ja",
    version: "1.3.0",
    sourceRev: SOURCE_REV,
    review: "machine-drafted",
    reviewers: [],
    updated: "2026-11-02",
  },
};

export function getLocaleMeta(tag: string): LocaleMeta | undefined {
  return LOCALE_META[tag];
}

/* True only for source English or explicitly human-reviewed locales.
 * Nothing in this programme may label machine-drafted output reviewed. */
export function isHumanVerified(tag: string): boolean {
  const meta = LOCALE_META[tag];
  return (
    meta !== undefined &&
    (meta.review === "source" || meta.review === "human-reviewed")
  );
}

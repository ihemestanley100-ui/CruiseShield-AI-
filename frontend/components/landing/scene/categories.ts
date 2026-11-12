/* World Atlas category registry: the six geographic regions plus the
 * two global network overlays (oceans, corridors). Data-only module
 * (no DOM, no three.js) so coverage rules stay unit-testable. */

export type AtlasCategoryKind = "region" | "ocean" | "corridor";

export interface AtlasCategory {
  id: string;
  kind: AtlasCategoryKind;
  name: string;
  blurb: string;
}

export const ATLAS_CATEGORIES: AtlasCategory[] = [
  { id: "north-america", kind: "region", name: "North America", blurb: "Regional hub marker and label." },
  { id: "south-america", kind: "region", name: "South America", blurb: "Regional hub marker and label." },
  { id: "europe", kind: "region", name: "Europe", blurb: "Regional hub marker and label." },
  { id: "africa", kind: "region", name: "Africa", blurb: "Regional hub marker and label." },
  { id: "middle-east", kind: "region", name: "Middle East", blurb: "Regional hub marker and label." },
  { id: "asia-pacific", kind: "region", name: "Asia Pacific", blurb: "Regional hub marker and label." },
  {
    id: "global-oceans",
    kind: "ocean",
    name: "Global Oceans",
    blurb: "Ocean-area annotation over the Pacific. Not a political region.",
  },
  {
    id: "cross-border-corridors",
    kind: "corridor",
    name: "Cross-Border Corridors",
    blurb:
      "Illustrative arcs between regions; synthetic data for demonstration only. Not real financial routes.",
  },
];

/** Mid-Pacific anchor, clear of every region hub. */
export const OCEAN_MARKER = { name: "Global Oceans", lat: -8, lon: -150 };

/** Illustrative endpoint pairs; resolved against REGION_HUBS by name. */
export const CORRIDOR_ROUTES: [string, string][] = [
  ["North America", "Europe"],
  ["Europe", "Middle East"],
  ["Middle East", "Asia Pacific"],
  ["Africa", "Middle East"],
  ["South America", "Africa"],
];

export function isValidGeo(lat: number, lon: number): boolean {
  return (
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    Math.abs(lat) <= 90 &&
    Math.abs(lon) <= 180
  );
}

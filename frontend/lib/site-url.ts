/** Deployment origin for absolute metadata URLs (openGraph images).
 *
 * J3 closeout (frontend EV38): when `NEXT_PUBLIC_SITE_URL` is set to the
 * deployed frontend origin (owner-supplied at staging), Next.js resolves
 * the relative brand-asset URLs in `layout.tsx` against it. When unset,
 * relative URLs are preserved (local/demo behavior unchanged).
 */
export function resolveMetadataBase(
  raw: string | undefined = process.env.NEXT_PUBLIC_SITE_URL,
): URL | undefined {
  const value = (raw ?? "").trim();
  if (!value) {
    return undefined;
  }
  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return undefined;
    }
    return url;
  } catch {
    return undefined;
  }
}

/* DI-10 privacy helpers. Masking is display-only; the backend
 * remains the authority on what may be shown. */

export function maskIp(value: string | null | undefined): string {
  if (!value) return "unknown";
  const trimmed = value.trim();
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(trimmed)) {
    const parts = trimmed.split(".");
    if (parts.every((p) => Number(p) <= 255)) {
      return `${parts[0]}.${parts[1]}.${parts[2]}.\u2022`;
    }
    return "unknown";
  }
  if (trimmed.includes(":")) {
    const groups = trimmed.split(":").filter((g) => g.length > 0);
    if (groups.length === 0) return "unknown";
    if (!groups.every((g) => /^[0-9a-fA-F]{1,4}$/.test(g))) return "unknown";
    return `${groups.slice(0, 4).join(":")}:\u2022`;
  }
  return "unknown";
}

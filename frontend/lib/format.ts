/* Money formatting mirrors the backend (integer minor units, no floats).
 * Grouping follows the caller's app locale; the default "en" keeps the
 * historic en-US output exactly. */

export function formatKobo(
  amountMinor: number,
  currency = "NGN",
  tag = "en"
): string {
  const major = amountMinor / 100;
  const symbol = currency === "NGN" ? "₦" : `${currency} `;
  let grouped: string;
  try {
    grouped = major.toLocaleString(tag, { maximumFractionDigits: 0 });
  } catch {
    grouped = major.toLocaleString("en", { maximumFractionDigits: 0 });
  }
  return `${symbol}${grouped}`;
}

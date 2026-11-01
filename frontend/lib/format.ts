/* Money formatting mirrors the backend (integer minor units, no floats). */

export function formatKobo(amountMinor: number, currency = "NGN"): string {
  const major = amountMinor / 100;
  const symbol = currency === "NGN" ? "₦" : `${currency} `;
  return `${symbol}${major.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })}`;
}

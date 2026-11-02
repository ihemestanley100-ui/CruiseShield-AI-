/* Locale-aware formatting over Intl: dates, numbers, money (integer
 * minor units, mirroring formatKobo — no floats), and relative time.
 * Every helper falls back to the fallback locale on bad input. */

import { FALLBACK_LOCALE } from "./dictionaries";

function safeTag(tag: string): string {
  try {
    return new Intl.Locale(tag).toString();
  } catch {
    return FALLBACK_LOCALE;
  }
}

export function formatDate(
  tag: string,
  value: Date | string,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = value instanceof Date ? value : new Date(value);
  try {
    return new Intl.DateTimeFormat(safeTag(tag), options).format(date);
  } catch {
    return new Intl.DateTimeFormat(FALLBACK_LOCALE, options).format(date);
  }
}

export function formatNumber(tag: string, value: number): string {
  try {
    return new Intl.NumberFormat(safeTag(tag)).format(value);
  } catch {
    return new Intl.NumberFormat(FALLBACK_LOCALE).format(value);
  }
}

/* Money: integer minor units in, locale-grouped major units out.
 * Currency symbol handling mirrors formatKobo (NGN -> ₦). */
export function formatMoney(
  tag: string,
  amountMinor: number,
  currency = "NGN"
): string {
  const major = amountMinor / 100;
  if (currency === "NGN") {
    return `₦${formatNumber(tag, major)}`;
  }
  try {
    return new Intl.NumberFormat(safeTag(tag), {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(major);
  } catch {
    return `${currency} ${formatNumber(FALLBACK_LOCALE, major)}`;
  }
}

export function formatRelative(
  tag: string,
  value: number,
  unit: Intl.RelativeTimeFormatUnit
): string {
  try {
    return new Intl.RelativeTimeFormat(safeTag(tag), {
      numeric: "auto",
    }).format(value, unit);
  } catch {
    return new Intl.RelativeTimeFormat(FALLBACK_LOCALE, {
      numeric: "auto",
    }).format(value, unit);
  }
}

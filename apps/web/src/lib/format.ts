/**
 * Centralized formatting helpers for consistent date, currency, and numerical presentation.
 */

export function formatDate(
  iso: string | null | undefined,
  locale = "en-IN",
  options: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" },
): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(locale, options);
  } catch {
    return iso;
  }
}

export function formatDateTime(
  iso: string | null | undefined,
  locale = "en-IN",
): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(locale, {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function formatCurrency(
  amount: string | number | null | undefined,
  currency = "INR",
  locale = "en-IN",
): string {
  if (amount === null || amount === undefined || amount === "") return "₹0.00";
  const num = typeof amount === "number" ? amount : parseFloat(amount);
  if (Number.isNaN(num)) return "₹0.00";

  try {
    const symbol = currency === "INR" ? "₹" : `${currency} `;
    return `${symbol}${num.toLocaleString(locale, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  } catch {
    return `₹${num.toFixed(2)}`;
  }
}

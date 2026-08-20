/**
 * Hex equivalents of app/globals.css's light-theme OKLCH tokens — Satori
 * (next/og's rendering engine) doesn't support the oklch() CSS function,
 * so ImageResponse routes can't reference the CSS variables directly.
 * Always the light palette: a generated OG/share card has one canonical
 * look regardless of the viewer's OS theme. Keep in sync with globals.css.
 */
export const OG_COLORS = {
  background: "#ffffff",
  foreground: "#0a0a0a",
  primary: "#464cb2",
  primaryForeground: "#f8f8f8",
  muted: "#f5f5f5",
  mutedForeground: "#737373",
  border: "#e5e5e5",
  destructive: "#c9302d",
} as const

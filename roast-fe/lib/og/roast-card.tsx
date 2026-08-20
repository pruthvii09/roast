import { ImageResponse } from "next/og"

import type { PublicRoast, Severity } from "@/lib/api/types"
import { OG_COLORS } from "@/lib/og/colors"

export const ROAST_CARD_SIZE = { width: 1200, height: 630 }

const SEVERITY_RANK: Record<Severity, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
  info: 0,
}

const SUBMISSION_TYPE_LABEL: Record<PublicRoast["submission"]["submission_type"], string> = {
  resume: "Resume",
  website: "Website",
  github: "GitHub Profile",
}

function pickHighlight(roast: PublicRoast): string {
  const text =
    roast.final_verdict ||
    [...roast.findings].sort((a, b) => SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity])[0]
      ?.roast_text ||
    roast.summary
  return text.length > 200 ? `${text.slice(0, 197)}...` : text
}

function FlameMark({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={OG_COLORS.primary} style={{ display: "flex" }}>
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
    </svg>
  )
}

/**
 * Shared by app/(public)/r/[token]/opengraph-image.tsx (for automatic
 * og:image meta-tag unfurling — its actual served URL gets a
 * build-generated hash suffix, e.g. opengraph-image-ygf4kt, so nothing
 * should hardcode that path) and app/(public)/r/[token]/card/route.tsx
 * (a stable URL for the "download image" button and any future reuse,
 * e.g. as a gallery thumbnail).
 */
export function renderRoastCard(roast: PublicRoast): ImageResponse {
  const submissionLabel = roast.submission.title || SUBMISSION_TYPE_LABEL[roast.submission.submission_type]

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: OG_COLORS.background,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <FlameMark size={32} />
          <span style={{ fontSize: 28, fontWeight: 600, color: OG_COLORS.foreground }}>
            Roast Anything
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          {roast.score !== null ? (
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, color: OG_COLORS.primary }}>
              <span style={{ fontSize: 72, fontWeight: 700 }}>{roast.score}</span>
              <span style={{ fontSize: 28, color: OG_COLORS.mutedForeground }}>/100</span>
            </div>
          ) : null}
          <span style={{ fontSize: 44, lineHeight: 1.25, fontWeight: 500, color: OG_COLORS.foreground }}>
            &ldquo;{pickHighlight(roast)}&rdquo;
          </span>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: 22,
            color: OG_COLORS.mutedForeground,
          }}
        >
          <span style={{ display: "flex" }}>{submissionLabel}</span>
          <span style={{ display: "flex" }}>AI-roasted, brutally honest</span>
        </div>
      </div>
    ),
    { ...ROAST_CARD_SIZE }
  )
}

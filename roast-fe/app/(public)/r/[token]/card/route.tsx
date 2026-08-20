import { fetchPublicRoast } from "@/lib/api/shares/get-public"
import { renderRoastCard } from "@/lib/og/roast-card"

export const revalidate = 3600

/**
 * GET /r/{token}/card — stable URL for the roast card PNG, used by the
 * "download image" button and any future reuse (e.g. a gallery
 * thumbnail). Renders the same card as opengraph-image.tsx, whose own
 * served URL Next.js suffixes with a build hash and so can't be
 * hardcoded anywhere.
 */
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  const roast = await fetchPublicRoast(token)
  return renderRoastCard(roast)
}

import { fetchPublicRoast } from "@/lib/api/shares/get-public"
import { renderRoastCard, ROAST_CARD_SIZE } from "@/lib/og/roast-card"

export const alt = "Roast Anything result card"
export const size = ROAST_CARD_SIZE
export const contentType = "image/png"
export const revalidate = 3600

export default async function Image({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  const roast = await fetchPublicRoast(token)
  return renderRoastCard(roast)
}

import { SharedRoastView } from "@/components/shared-roast/shared-roast-view"

export default async function SharedRoastPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  return <SharedRoastView token={token} />
}

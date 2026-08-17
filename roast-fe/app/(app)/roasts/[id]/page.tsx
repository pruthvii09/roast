import { RoastResult } from "@/components/roast-result/roast-result"

export default async function RoastResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <RoastResult roastId={id} />
}

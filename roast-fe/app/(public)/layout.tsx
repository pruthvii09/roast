import { ShareTopbar } from "@/components/shared-roast/share-topbar"

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <ShareTopbar />
      <main className="mx-auto w-full max-w-5xl px-4 sm:px-6 flex-1 py-8 sm:py-10">{children}</main>
    </>
  )
}

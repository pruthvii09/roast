import { ShareTopbar } from "@/components/shared-roast/share-topbar"

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <ShareTopbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">{children}</main>
    </>
  )
}

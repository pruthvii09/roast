import Link from "next/link"

import { Logo } from "@/components/shared/logo"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative flex min-h-full flex-1 flex-col items-center justify-center gap-8 overflow-hidden px-6 py-16">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,var(--border)_1px,transparent_0)] bg-size-[32px_32px] opacity-60 [mask-image:radial-gradient(ellipse_60%_60%_at_50%_0%,black_30%,transparent_80%)]" />
        <div className="absolute top-[-10rem] left-1/2 h-[30rem] w-[40rem] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,color-mix(in_oklch,var(--primary)_12%,transparent),transparent)] blur-3xl" />
      </div>
      <Link href="/">
        <Logo />
      </Link>
      {children}
    </main>
  )
}

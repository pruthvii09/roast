import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Logo } from "@/components/shared/logo"

/**
 * Public share page's only chrome — presentational, no auth dependency
 * (mirrors components/layout/header.tsx), but sized to (public)/layout.tsx's
 * max-w-3xl column instead of Header's max-w-5xl, and pointed at "/" rather
 * than "/register" directly since a share-page visitor hasn't seen any of
 * the marketing pitch yet.
 */
function ShareTopbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-3xl items-center justify-between px-6">
        <Link href="/" className="shrink-0">
          <Logo />
        </Link>
        <nav className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          <Button
            render={<Link href="/wall-of-fame" />}
            nativeButton={false}
            variant="ghost"
            size="sm"
            className="rounded-full"
          >
            Wall of Fame
          </Button>
          <Button
            render={<Link href="/login" />}
            nativeButton={false}
            variant="ghost"
            size="sm"
            className="rounded-full"
          >
            Log in
          </Button>
          <Button
            render={<Link href="/" />}
            nativeButton={false}
            size="sm"
            className="rounded-full px-4 shadow-sm"
          >
            Roast yours too
          </Button>
        </nav>
      </div>
    </header>
  )
}

export { ShareTopbar }

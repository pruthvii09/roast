import Link from "next/link"
import { LogIn, Menu, Trophy } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="shrink-0">
          <Logo />
        </Link>
        <nav className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger
              className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground outline-none hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 sm:hidden"
              aria-label="More"
            >
              <Menu className="size-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" sideOffset={8}>
              <DropdownMenuItem render={<Link href="/wall-of-fame" />}>
                <Trophy />
                Wall of Fame
              </DropdownMenuItem>
              <DropdownMenuItem render={<Link href="/login" />}>
                <LogIn />
                Log in
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button
            render={<Link href="/wall-of-fame" />}
            nativeButton={false}
            variant="ghost"
            size="sm"
            className="hidden rounded-full sm:inline-flex"
          >
            Wall of Fame
          </Button>
          <Button
            render={<Link href="/login" />}
            nativeButton={false}
            variant="ghost"
            size="sm"
            className="hidden rounded-full sm:inline-flex"
          >
            Log in
          </Button>
          <Button
            render={<Link href="/" />}
            nativeButton={false}
            size="sm"
            className="rounded-full px-4 shadow-sm"
          >
            <span className="hidden sm:inline">Roast yours too</span>
            <span className="sm:hidden">Roast mine</span>
          </Button>
        </nav>
      </div>
    </header>
  )
}

export { ShareTopbar }

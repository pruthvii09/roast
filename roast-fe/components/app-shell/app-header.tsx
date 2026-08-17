"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Plus } from "lucide-react"

import { MobileNav } from "@/components/app-shell/mobile-nav"
import { NAV_LINKS } from "@/components/app-shell/nav-links"
import { useNewRoast } from "@/components/app-shell/new-roast-context"
import { UserMenu } from "@/components/app-shell/user-menu"
import { Logo } from "@/components/shared/logo"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function AppHeader() {
  const pathname = usePathname()
  const { open } = useNewRoast()

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="shrink-0">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {NAV_LINKS.map(({ href, label }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`)
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            className="hidden rounded-full px-4 shadow-sm sm:inline-flex"
            onClick={() => open()}
          >
            <Plus />
            New Roast
          </Button>
          <UserMenu />
          <div className="md:hidden">
            <MobileNav />
          </div>
        </div>
      </div>
    </header>
  )
}

export { AppHeader }

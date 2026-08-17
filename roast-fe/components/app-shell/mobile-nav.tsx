"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { Menu, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Logo } from "@/components/shared/logo"
import { NAV_LINKS } from "@/components/app-shell/nav-links"
import { useNewRoast } from "@/components/app-shell/new-roast-context"
import { cn } from "@/lib/utils"

function MobileNav() {
  const pathname = usePathname()
  const { open: openNewRoast } = useNewRoast()
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger render={<Button variant="ghost" size="icon-sm" aria-label="Open menu" />}>
        <Menu />
      </SheetTrigger>
      <SheetContent side="left" className="w-72 max-w-[85vw]">
        <SheetHeader>
          <Logo />
          <SheetTitle className="sr-only">Navigation menu</SheetTitle>
        </SheetHeader>
        <nav className="flex flex-col gap-1">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`)
            return (
              <SheetClose key={href} render={<Link href={href} />} nativeButton={false}>
                <span
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-foreground hover:bg-muted"
                  )}
                >
                  <Icon className="size-4" />
                  {label}
                </span>
              </SheetClose>
            )
          })}
        </nav>
        <SheetClose render={<Button className="rounded-full" onClick={() => openNewRoast()} />}>
          <Plus />
          New Roast
        </SheetClose>
      </SheetContent>
    </Sheet>
  )
}

export { MobileNav }

import Link from "next/link"

import { Container } from "@/components/shared/container"
import { Logo } from "@/components/shared/logo"

const FOOTER_COLUMNS = [
  {
    heading: "Product",
    links: [
      { label: "Roast Mine", href: "/register" },
      { label: "See an example", href: "/#example-roast" },
      { label: "Log in", href: "/login" },
    ],
  },
  {
    heading: "Legal",
    links: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
] as const

export function Footer() {
  return (
    <footer className="overflow-hidden border-t border-border bg-card">
      <Container className="grid gap-10 py-14 sm:grid-cols-[1.5fr_1fr_1fr]">
        <div className="flex flex-col items-center gap-2 text-center sm:items-start sm:text-left">
          <Logo />
          <p className="max-w-[22ch] text-sm text-muted-foreground">
            Built for people brave enough to ask.
          </p>
        </div>
        {FOOTER_COLUMNS.map((column) => (
          <nav
            key={column.heading}
            className="flex flex-col items-center gap-3 text-center sm:items-start sm:text-left"
          >
            <span className="font-mono text-xs tracking-widest text-muted-foreground uppercase">
              {column.heading}
            </span>
            <ul className="flex flex-col items-center gap-2 sm:items-start">
              {column.links.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-foreground/80 transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </Container>
      <div className="border-t border-border">
        <Container className="flex flex-col items-center justify-between gap-2 py-4 text-center sm:flex-row sm:text-left">
          <span className="font-mono text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Roast Anything
          </span>
          <span className="font-mono text-xs text-muted-foreground">
            All roasts are cooked fresh.
          </span>
        </Container>
      </div>
      <div
        aria-hidden
        className="pointer-events-none select-none pb-2 text-center font-display text-[22vw] leading-none font-medium text-foreground/[0.035] sm:text-[13vw]"
      >
        Roast Anything
      </div>
    </footer>
  )
}

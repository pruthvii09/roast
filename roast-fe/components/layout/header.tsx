"use client"

import Link from "next/link"

import { UserMenu } from "@/components/app-shell/user-menu"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/shared/logo"
import { useAuth } from "@/providers/auth-provider"

export function Header() {
  const { status } = useAuth()

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between px-4 sm:px-6">
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
          {status === "authenticated" ? (
            <>
              <Button
                render={<Link href="/dashboard" />}
                nativeButton={false}
                size="sm"
                className="rounded-full px-4 shadow-sm"
              >
                Dashboard
              </Button>
              <UserMenu />
            </>
          ) : status === "unauthenticated" ? (
            <>
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
                render={<Link href="/register" />}
                nativeButton={false}
                size="sm"
                className="rounded-full px-4 shadow-sm"
              >
                Sign up
              </Button>
            </>
          ) : (
            <div className="h-9 w-24 animate-pulse rounded-full bg-muted" aria-hidden />
          )}
        </nav>
      </div>
    </header>
  )
}

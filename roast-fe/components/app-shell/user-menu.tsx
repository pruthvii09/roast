"use client"

import Link from "next/link"
import { useState } from "react"
import { Loader2, LogOut, User } from "lucide-react"
import { toast } from "sonner"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/providers/auth-provider"

function initialsFrom(name: string, email: string): string {
  const source = name.trim() || email
  const parts = source.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return source.slice(0, 2).toUpperCase()
}

function UserMenu() {
  const { user, logout } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
      toast.success("Logged out")
    } catch {
      toast.error("Couldn't confirm logout with the server", {
        description: "You're signed out on this device, but the session may still be active elsewhere.",
      })
    } finally {
      setLoggingOut(false)
    }
  }

  if (!user) {
    return <Avatar className="animate-pulse bg-muted" />
  }

  const initials = initialsFrom(user.display_name, user.email)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="rounded-full outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        aria-label="Account menu"
      >
        <Avatar>
          {user.avatar_url ? <AvatarImage src={user.avatar_url} alt="" /> : null}
          <AvatarFallback>{initials}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={8} className="w-56">
        <div className="flex flex-col gap-0.5 px-2 py-1.5">
          <span className="truncate text-sm font-medium text-foreground">
            {user.display_name || "Your account"}
          </span>
          <span className="truncate text-xs font-normal text-muted-foreground">
            {user.email}
          </span>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href="/profile" />}>
          <User />
          Profile
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" disabled={loggingOut} onClick={handleLogout}>
          {loggingOut ? <Loader2 className="animate-spin" /> : <LogOut />}
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export { UserMenu }

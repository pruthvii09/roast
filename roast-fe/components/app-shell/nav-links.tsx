import { Flame, LayoutDashboard, User } from "lucide-react"

export const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/roasts", label: "My Roasts", icon: Flame },
  { href: "/profile", label: "Profile", icon: User },
] as const

import { Flame, LayoutDashboard, Trophy, User } from "lucide-react"

export const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/roasts", label: "My Roasts", icon: Flame },
  { href: "/wall-of-fame", label: "Wall of Fame", icon: Trophy },
  { href: "/profile", label: "Profile", icon: User },
] as const

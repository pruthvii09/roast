"use client"

import Link from "next/link"
import { ArrowRight } from "lucide-react"

import { ActivityList } from "@/components/dashboard/activity-list"
import { InviteFriendsCard } from "@/components/dashboard/invite-friends-card"
import { NewRoastOptions } from "@/components/dashboard/new-roast-options"
import { RoastQuotaBadge } from "@/components/dashboard/roast-quota-badge"
import { useAuth } from "@/providers/auth-provider"

const RECENT_PAGE_SIZE = 5

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="font-mono text-xs tracking-widest text-primary uppercase">Dashboard</p>
          <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">
            {user ? `Hey ${user.display_name || user.email.split("@")[0]}.` : "Welcome back."}
          </h1>
        </div>
        <RoastQuotaBadge />
      </div>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">What can I roast?</h2>
        <NewRoastOptions />
      </section>

      <InviteFriendsCard />

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold text-foreground">Recent roasts</h2>
          <Link
            href="/roasts"
            className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            View all
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
        <ActivityList pageSize={RECENT_PAGE_SIZE} />
      </section>
    </div>
  )
}

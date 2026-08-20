import { AppHeader } from "@/components/app-shell/app-header"
import { NewRoastProvider } from "@/components/app-shell/new-roast-context"
import { ReferralBonusBanner } from "@/components/app-shell/referral-bonus-banner"
import { ProtectedGate } from "@/components/auth/protected-gate"
import { Container } from "@/components/shared/container"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedGate>
      <NewRoastProvider>
        <AppHeader />
        <ReferralBonusBanner />
        <Container className="flex-1 py-8 sm:py-10">{children}</Container>
      </NewRoastProvider>
    </ProtectedGate>
  )
}

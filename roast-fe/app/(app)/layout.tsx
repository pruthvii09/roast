import { AppHeader } from "@/components/app-shell/app-header"
import { NewRoastProvider } from "@/components/app-shell/new-roast-context"
import { ProtectedGate } from "@/components/auth/protected-gate"
import { Container } from "@/components/shared/container"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedGate>
      <NewRoastProvider>
        <AppHeader />
        <Container className="flex-1 py-8 sm:py-10">{children}</Container>
      </NewRoastProvider>
    </ProtectedGate>
  )
}

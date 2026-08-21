import type { Metadata } from "next"

import { GadbadBanner } from "@/components/marketing/gadbad-banner"
import { Container } from "@/components/shared/container"

export const metadata: Metadata = {
  title: "Privacy Policy — Roast Anything",
  description:
    "What Roast Anything collects, why, and what we do with your resume, website, GitHub profile, and dignity.",
}

const SECTIONS = [
  {
    heading: "1. The short, non-lawyer version",
    body: [
      "You give us your resume, website, or GitHub profile. We run it through an AI that says mean-but-useful things about it. We keep the minimum we need to run your account and make the product better. We don't sell your data. That's the whole deal — the rest of this page is just the legally required fine print.",
    ],
  },
  {
    heading: "2. What we collect",
    body: [
      "Account info: your email address and a hashed password. We never store your password in plain text, because that would be a much worse roast target than your resume.",
      "Submitted content: whatever you give us to be roasted — an uploaded resume file, a website URL, or a GitHub username/profile.",
      "Generated content: the roast we produce from that submission, plus any reactions, shares, or \"feature on the Wall of Fame\" choices you make about it.",
      "Usage data: your weekly roast quota (limit, used, remaining, reset time), referral codes you've used or generated, and basic activity like login timestamps.",
      "Technical data: session/auth tokens (cookies), IP address, and device/browser info, collected automatically for security and to keep you logged in.",
    ],
  },
  {
    heading: "3. How we use it",
    body: [
      "To generate your roast and show it back to you.",
      "To run your account: email verification via one-time codes (OTP), password resets, and login sessions.",
      "To enforce and track your weekly roast quota, and to grant temporary bonus quota when you refer a friend.",
      "To display roasts you've explicitly chosen to make public — for example, on a shareable roast card or the Wall of Fame.",
      "To keep the service secure, debug issues, and improve roast quality over time.",
    ],
  },
  {
    heading: "4. AI processing & other services we use",
    body: [
      "Generating a roast means sending your submitted content (resume text, website content, or GitHub profile data) to OpenAI for processing. That transfer is governed by OpenAI's own privacy and data-usage policies; we don't use your content to train our own models, and API-submitted content is not used by OpenAI to train theirs.",
      "We use a transactional email provider (currently Resend) to send OTP codes and password-reset emails. That means your email address is shared with them for the sole purpose of delivering those emails.",
      "We don't sell your data to advertisers, data brokers, or anyone else. If that ever changes, this policy — and the law, in most places — requires us to tell you first.",
    ],
  },
  {
    heading: "5. Public roasts & the Wall of Fame",
    body: [
      "Roasts are private by default — only you can see them. If you generate a shareable roast card or feature a roast on the Wall of Fame, that content (and only that content, not your account details) becomes publicly visible to anyone with the link or browsing the gallery.",
      "You can un-feature or stop sharing a roast at any time from your dashboard. Removing it takes it down from the Wall of Fame going forward, though copies already shared or cached elsewhere (screenshots, saved links) are out of our hands — the internet has a long memory, much like a good roast.",
    ],
  },
  {
    heading: "6. How long we keep things",
    body: [
      "We keep your account and submitted content for as long as your account is active. If you delete your account, we delete your personal data and private roasts within a reasonable period, except where we're required to retain limited records for legal, security, or fraud-prevention purposes.",
    ],
  },
  {
    heading: "7. Your rights",
    body: [
      "Depending on where you live, you may have the right to access, correct, export, or delete the personal data we hold about you. You can handle most of this yourself from your account settings; for anything else, email us and we'll sort it out — no roast necessary.",
    ],
  },
  {
    heading: "8. Cookies & sessions",
    body: [
      "We use strictly necessary cookies/tokens to keep you logged in and to protect your account. We don't use third-party advertising or tracking cookies.",
    ],
  },
  {
    heading: "9. Children's privacy",
    body: [
      "Roast Anything isn't directed at children, and you must be at least 13 years old (or the minimum age required in your country) to use it. If we learn we've collected data from a child under that age, we'll delete it.",
    ],
  },
  {
    heading: "10. Changes to this policy",
    body: [
      "If we materially change how we handle your data, we'll update this page and, where required, notify you directly. Continuing to use Roast Anything after changes take effect means you accept the update.",
    ],
  },
  {
    heading: "11. Contact",
    body: [
      "Questions, requests, or complaints about your data? Reach us at hello@roastanything.com.",
    ],
  },
] as const

export default function PrivacyPage() {
  return (
    <Container className="max-w-3xl py-16 sm:py-20">
      <div className="space-y-2 text-center sm:text-left">
        <h1 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          Privacy Policy
        </h1>
        <p className="font-mono text-xs tracking-widest text-muted-foreground uppercase">
          Last updated August 21, 2026
        </p>
      </div>

      <div className="mt-8">
        <GadbadBanner />
      </div>

      <div className="mt-2 space-y-10">
        {SECTIONS.map((section) => (
          <section key={section.heading} className="space-y-3">
            <h2 className="font-display text-lg font-medium text-foreground">
              {section.heading}
            </h2>
            {section.body.map((paragraph, i) => (
              <p key={i} className="text-sm leading-relaxed text-foreground/80">
                {paragraph}
              </p>
            ))}
          </section>
        ))}
      </div>
    </Container>
  )
}

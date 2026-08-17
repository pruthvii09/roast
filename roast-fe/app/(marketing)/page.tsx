import type { Metadata } from "next"

import { ExampleRoast } from "@/components/marketing/example-roast"
import { FinalCta } from "@/components/marketing/final-cta"
import { Hero } from "@/components/marketing/hero"
import { HowItWorks } from "@/components/marketing/how-it-works"
import { Languages } from "@/components/marketing/languages"
import { RoastPreview } from "@/components/marketing/roast-preview"
import { RoastStyles } from "@/components/marketing/roast-styles"
import { SubmissionTypes } from "@/components/marketing/submission-types"

export const metadata: Metadata = {
  title:
    "Roast Anything — Brutally honest feedback on your resume, website, or GitHub",
  description:
    "Submit your resume, website, or GitHub profile and get an AI-generated roast with feedback you can actually use.",
  openGraph: {
    title: "Roast Anything",
    description:
      "Brutally honest, actually useful feedback on your resume, website, or GitHub.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Roast Anything",
    description:
      "Brutally honest, actually useful feedback on your resume, website, or GitHub.",
  },
}

export default function HomePage() {
  return (
    <>
      <Hero />
      <RoastPreview />
      <SubmissionTypes />
      <HowItWorks />
      <RoastStyles />
      <Languages />
      <ExampleRoast />
      <FinalCta />
    </>
  )
}

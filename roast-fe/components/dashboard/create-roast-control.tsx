"use client"

import { useState } from "react"
import { Loader2, Sparkles } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateRoastRunMutation } from "@/lib/api/roasts/queries"
import type { Intensity, Language } from "@/lib/api/types"

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "hinglish", label: "Hinglish" },
]

const INTENSITY_OPTIONS: { value: Intensity; label: string }[] = [
  { value: "gentle", label: "Gentle" },
  { value: "sarcastic", label: "Sarcastic" },
  { value: "brutal", label: "Brutal" },
  { value: "nuclear", label: "Nuclear" },
]

const LANGUAGE_LABEL = Object.fromEntries(LANGUAGE_OPTIONS.map((o) => [o.value, o.label]))
const INTENSITY_LABEL = Object.fromEntries(INTENSITY_OPTIONS.map((o) => [o.value, o.label]))

function CreateRoastControl({ submissionId }: { submissionId: string }) {
  const [language, setLanguage] = useState<Language>("en")
  const [intensity, setIntensity] = useState<Intensity>("sarcastic")
  const createRoast = useCreateRoastRunMutation(submissionId)

  async function handleCreate() {
    try {
      await createRoast.mutateAsync({ language, intensity })
      toast.success("Roast requested", { description: "We'll have it ready shortly." })
    } catch (error) {
      toast.error("Couldn't start that roast", { description: getApiErrorMessage(error) })
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-border p-3">
      <Select value={language} onValueChange={(value) => setLanguage(value as Language)}>
        <SelectTrigger size="sm" className="w-28">
          <SelectValue>{(value: Language) => LANGUAGE_LABEL[value]}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {LANGUAGE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={intensity} onValueChange={(value) => setIntensity(value as Intensity)}>
        <SelectTrigger size="sm" className="w-32">
          <SelectValue>{(value: Intensity) => INTENSITY_LABEL[value]}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {INTENSITY_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        size="sm"
        className="rounded-full"
        onClick={handleCreate}
        disabled={createRoast.isPending}
      >
        {createRoast.isPending ? <Loader2 className="animate-spin" /> : <Sparkles />}
        Roast it
      </Button>
    </div>
  )
}

export { CreateRoastControl }

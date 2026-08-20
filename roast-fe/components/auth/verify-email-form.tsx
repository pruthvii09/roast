"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { REGEXP_ONLY_DIGITS } from "input-otp"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp"
import { isApiError } from "@/lib/api/errors"
import { applyApiFieldErrors, getApiErrorMessage } from "@/lib/api/form-errors"
import { getSafeNextPath } from "@/lib/auth-redirect"
import { useResendVerificationMutation } from "@/lib/api/auth/queries"
import { useAuth } from "@/providers/auth-provider"

const RESEND_COOLDOWN_SECONDS = 60

const verifyEmailSchema = z.object({
  code: z.string().length(6, "Enter the 6-digit code."),
})

type VerifyEmailFormValues = z.infer<typeof verifyEmailSchema>

function VerifyEmailForm() {
  const { status, verifyEmail } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const resendMutation = useResendVerificationMutation()
  const [formError, setFormError] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(0)

  const email = searchParams.get("email") ?? ""
  const next = getSafeNextPath(searchParams.get("next"))

  const form = useForm<VerifyEmailFormValues>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: { code: "" },
  })

  useEffect(() => {
    if (status === "authenticated") router.replace(next)
  }, [status, router, next])

  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => setCooldown((seconds) => Math.max(0, seconds - 1)), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  if (!email) {
    return (
      <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-medium">Missing email</CardTitle>
          <CardDescription>
            We couldn&apos;t tell which account to verify. Try registering or logging in again.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Link href="/register" className="text-sm text-primary underline-offset-4 hover:underline">
            Back to sign up
          </Link>
        </CardFooter>
      </Card>
    )
  }

  async function onSubmit(values: VerifyEmailFormValues) {
    setFormError(null)
    try {
      await verifyEmail({ email, code: values.code })
      toast.success("Email verified")
      router.replace(next)
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) setFormError(getApiErrorMessage(error))
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  async function handleResend() {
    try {
      await resendMutation.mutateAsync({ email })
      toast.success("Code sent", { description: "Check your inbox for a new code." })
      setCooldown(RESEND_COOLDOWN_SECONDS)
    } catch (error) {
      toast.error("Couldn't resend the code", { description: getApiErrorMessage(error) })
    }
  }

  return (
    <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-2xl font-medium">Verify your email</CardTitle>
        <CardDescription>
          Enter the 6-digit code we sent to <span className="font-medium text-foreground">{email}</span>.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {formError ? (
          <Alert variant="destructive">
            <AlertDescription>{formError}</AlertDescription>
          </Alert>
        ) : null}
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem className="flex flex-col items-center">
                  <FormControl>
                    <InputOTP
                      maxLength={6}
                      pattern={REGEXP_ONLY_DIGITS}
                      autoFocus
                      value={field.value}
                      onChange={field.onChange}
                    >
                      <InputOTPGroup>
                        {[0, 1, 2, 3, 4, 5].map((index) => (
                          <InputOTPSlot key={index} index={index} />
                        ))}
                      </InputOTPGroup>
                    </InputOTP>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="w-full rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Verify
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="justify-center">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleResend}
          disabled={cooldown > 0 || resendMutation.isPending}
        >
          {resendMutation.isPending ? <Loader2 className="animate-spin" /> : null}
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
        </Button>
      </CardFooter>
    </Card>
  )
}

export { VerifyEmailForm }

"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2, Sparkles } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { PasswordInput } from "@/components/auth/password-input"
import { CardSkeleton } from "@/components/shared/loading-skeletons"
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { isApiError } from "@/lib/api/errors"
import { applyApiFieldErrors, getAuthErrorMessage } from "@/lib/api/auth/form-errors"
import { getSafeNextPath } from "@/lib/auth-redirect"
import { useAuth } from "@/providers/auth-provider"

// Client-side checks improve UX (fail fast, no round trip) but the backend
// remains authoritative — Django additionally runs UserAttributeSimilarity,
// CommonPassword, and Numeric password validators that aren't replicated
// here; their messages surface verbatim via applyApiFieldErrors instead.
const registerSchema = z
  .object({
    display_name: z.string().max(150, "Keep it under 150 characters.").optional(),
    email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
    password: z.string().min(10, "Use at least 10 characters."),
    confirmPassword: z.string().min(1, "Confirm your password."),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match.",
    path: ["confirmPassword"],
  })

type RegisterFormValues = z.infer<typeof registerSchema>

// Loose client-side sanity check only — real codes are 8 uppercase
// alphanumeric chars, but any garbage that slips past this is still
// handled safely server-side (an unknown code is a silent no-op, see
// apps.referrals.services.redeem_referral_code's docstring). This just
// avoids forwarding an obviously-mangled query param.
const REFERRAL_CODE_PATTERN = /^[A-Za-z0-9]{1,32}$/

function getReferralCode(raw: string | null): string | undefined {
  if (!raw || !REFERRAL_CODE_PATTERN.test(raw)) return undefined
  return raw
}

function RegisterForm() {
  const { status, register: registerUser } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [formError, setFormError] = useState<string | null>(null)
  const next = getSafeNextPath(searchParams.get("next"))
  const referralCode = getReferralCode(searchParams.get("ref"))

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { display_name: "", email: "", password: "", confirmPassword: "" },
  })

  useEffect(() => {
    if (status === "authenticated") router.replace(next)
  }, [status, router, next])

  if (status === "loading" || status === "authenticated") {
    return (
      <div className="w-full max-w-sm">
        <CardSkeleton />
      </div>
    )
  }

  async function onSubmit(values: RegisterFormValues) {
    setFormError(null)
    try {
      await registerUser({
        email: values.email,
        password: values.password,
        display_name: values.display_name?.trim() || undefined,
        referral_code: referralCode,
      })
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) setFormError(getAuthErrorMessage(error))
      } else {
        setFormError(getAuthErrorMessage(error))
      }
      return
    }

    // Registration never returns tokens, and now the account can't log in
    // until its email is verified anyway (see apps.accounts.serializers.
    // LoginSerializer) — go straight to the OTP step instead of attempting
    // a login that would just fail.
    toast.success("Account created", { description: "Check your inbox for a verification code." })
    router.replace(
      `/verify-email?email=${encodeURIComponent(values.email)}&next=${encodeURIComponent(next)}`
    )
  }

  return (
    <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-2xl font-medium">Create an account</CardTitle>
        <CardDescription>Submit something. Get roasted.</CardDescription>
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
              name="display_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input autoComplete="name" placeholder="What should we call you?" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      autoComplete="email"
                      placeholder="you@example.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      autoComplete="new-password"
                      placeholder="At least 10 characters"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm password</FormLabel>
                  <FormControl>
                    <PasswordInput autoComplete="new-password" placeholder="Type it again" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {referralCode ? (
              <p className="flex items-center justify-center gap-1.5 text-center text-sm font-medium text-primary">
                <Sparkles className="size-4" aria-hidden />
                You&apos;ll get +1 bonus roast this week
              </p>
            ) : null}
            <Button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="w-full rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Create account
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary underline-offset-4 hover:underline">
            Log in
          </Link>
        </p>
      </CardFooter>
    </Card>
  )
}

export { RegisterForm }

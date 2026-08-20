"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { REGEXP_ONLY_DIGITS } from "input-otp"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { PasswordInput } from "@/components/auth/password-input"
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
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp"
import { isApiError } from "@/lib/api/errors"
import { applyApiFieldErrors, getApiErrorMessage } from "@/lib/api/form-errors"
import { useConfirmPasswordResetMutation } from "@/lib/api/auth/queries"

// Same client-side-only-improves-UX reasoning as register-form.tsx's schema
// comment — the backend's validate_password validators remain authoritative.
const resetPasswordSchema = z
  .object({
    code: z.string().length(6, "Enter the 6-digit code."),
    new_password: z.string().min(10, "Use at least 10 characters."),
    confirmPassword: z.string().min(1, "Confirm your password."),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords don't match.",
    path: ["confirmPassword"],
  })

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const confirmReset = useConfirmPasswordResetMutation()
  const [formError, setFormError] = useState<string | null>(null)

  const email = searchParams.get("email") ?? ""

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { code: "", new_password: "", confirmPassword: "" },
  })

  if (!email) {
    return (
      <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-medium">Missing email</CardTitle>
          <CardDescription>
            We couldn&apos;t tell which account to reset. Request a new code to continue.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Link href="/forgot-password" className="text-sm text-primary underline-offset-4 hover:underline">
            Request reset code
          </Link>
        </CardFooter>
      </Card>
    )
  }

  async function onSubmit(values: ResetPasswordFormValues) {
    setFormError(null)
    try {
      await confirmReset.mutateAsync({ email, code: values.code, new_password: values.new_password })
      toast.success("Password reset", { description: "Please log in with your new password." })
      router.replace("/login")
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) form.setError("code", { type: "server", message: "That code is incorrect or expired." })
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  return (
    <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-2xl font-medium">Reset your password</CardTitle>
        <CardDescription>
          Enter the code we sent to <span className="font-medium text-foreground">{email}</span> and choose a
          new password.
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
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
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
            <Button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="w-full rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Reset password
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

export { ResetPasswordForm }

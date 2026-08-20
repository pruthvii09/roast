"use client"

import Link from "next/link"
import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { CheckCircle2, Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { z } from "zod"

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
import { Input } from "@/components/ui/input"
import { useRequestPasswordResetMutation } from "@/lib/api/auth/queries"

const forgotPasswordSchema = z.object({
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
})

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>

function ForgotPasswordForm() {
  const requestReset = useRequestPasswordResetMutation()
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null)

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  })

  async function onSubmit(values: ForgotPasswordFormValues) {
    // Always succeeds from the caller's perspective — the backend never
    // reveals whether the account exists (see RequestPasswordResetView).
    await requestReset.mutateAsync(values)
    setSubmittedEmail(values.email)
  }

  if (submittedEmail) {
    return (
      <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
        <CardHeader className="items-center text-center">
          <span className="flex size-10 items-center justify-center rounded-full bg-success/10 text-success">
            <CheckCircle2 className="size-5" />
          </span>
          <CardTitle className="font-display text-2xl font-medium">Check your email</CardTitle>
          <CardDescription>
            If an account exists for <span className="font-medium text-foreground">{submittedEmail}</span>,
            we&apos;ve sent a reset code.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Button
            render={<Link href={`/reset-password?email=${encodeURIComponent(submittedEmail)}`} />}
            nativeButton={false}
            className="rounded-full px-6"
          >
            Enter code
          </Button>
        </CardFooter>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-2xl font-medium">Forgot password</CardTitle>
        <CardDescription>We&apos;ll email you a code to reset it.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
            <Button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="w-full rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Send reset code
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="justify-center">
        <Link href="/login" className="text-sm text-primary underline-offset-4 hover:underline">
          Back to log in
        </Link>
      </CardFooter>
    </Card>
  )
}

export { ForgotPasswordForm }

"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
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

const loginSchema = z.object({
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
})

type LoginFormValues = z.infer<typeof loginSchema>

function LoginForm() {
  const { status, login } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [formError, setFormError] = useState<string | null>(null)
  const next = getSafeNextPath(searchParams.get("next"))

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
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

  async function onSubmit(values: LoginFormValues) {
    setFormError(null)
    try {
      await login(values)
      toast.success("Welcome back")
      router.replace(next)
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) setFormError(getAuthErrorMessage(error))
      } else {
        setFormError(getAuthErrorMessage(error))
      }
    }
  }

  return (
    <Card className="w-full max-w-sm rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-2xl font-medium">Welcome back</CardTitle>
        <CardDescription>Log in to see your roasts.</CardDescription>
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
                    <PasswordInput autoComplete="current-password" {...field} />
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
              Log in
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary underline-offset-4 hover:underline">
            Sign up
          </Link>
        </p>
      </CardFooter>
    </Card>
  )
}

export { LoginForm }

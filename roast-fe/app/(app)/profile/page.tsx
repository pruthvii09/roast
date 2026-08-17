"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { PasswordInput } from "@/components/auth/password-input"
import { ErrorState } from "@/components/shared/error-state"
import { CardSkeleton } from "@/components/shared/loading-skeletons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
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
import { applyApiFieldErrors, getApiErrorMessage } from "@/lib/api/form-errors"
import { useChangePasswordMutation, useMeQuery, useUpdateMeMutation } from "@/lib/api/auth/queries"
import type { User } from "@/lib/api/types"
import { useAuth } from "@/providers/auth-provider"

const profileSchema = z.object({
  display_name: z.string().max(150, "Keep it under 150 characters.").optional(),
})
type ProfileFormValues = z.infer<typeof profileSchema>

const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Enter your current password."),
    new_password: z.string().min(10, "Use at least 10 characters."),
    confirm_new_password: z.string().min(1, "Confirm your new password."),
  })
  .refine((data) => data.new_password === data.confirm_new_password, {
    message: "Passwords don't match.",
    path: ["confirm_new_password"],
  })
type PasswordFormValues = z.infer<typeof passwordSchema>

function initialsFrom(name: string, email: string): string {
  const source = name.trim() || email
  const parts = source.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return source.slice(0, 2).toUpperCase()
}

function ProfileForm({ user }: { user: User }) {
  const [formError, setFormError] = useState<string | null>(null)
  const updateMe = useUpdateMeMutation()

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { display_name: user.display_name },
  })

  // Re-sync if the cached user changes (e.g. a background refetch) after mount.
  useEffect(() => {
    form.reset({ display_name: user.display_name })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  async function onSubmit(values: ProfileFormValues) {
    setFormError(null)
    try {
      await updateMe.mutateAsync({ display_name: values.display_name ?? "" })
      toast.success("Profile updated")
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) setFormError(getApiErrorMessage(error))
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  return (
    <Card className="rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Avatar size="lg">
            <AvatarFallback>{initialsFrom(user.display_name, user.email)}</AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="font-display text-xl font-medium">Profile</CardTitle>
            <CardDescription>{user.email}</CardDescription>
          </div>
        </div>
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
                  <FormLabel>Display name</FormLabel>
                  <FormControl>
                    <Input placeholder="What should we call you?" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Save changes
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

function ChangePasswordForm() {
  const router = useRouter()
  const { logout } = useAuth()
  const [formError, setFormError] = useState<string | null>(null)
  const changePassword = useChangePasswordMutation()

  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { old_password: "", new_password: "", confirm_new_password: "" },
  })

  async function onSubmit(values: PasswordFormValues) {
    setFormError(null)
    try {
      await changePassword.mutateAsync({
        old_password: values.old_password,
        new_password: values.new_password,
      })
      toast.success("Password changed", { description: "Please log in again." })
      await logout()
      router.replace("/login")
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(form, error.details)
        if (!applied) setFormError(getApiErrorMessage(error))
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  return (
    <Card className="rounded-2xl border-none shadow-xl shadow-foreground/6 ring-1 ring-border">
      <CardHeader>
        <CardTitle className="font-display text-xl font-medium">Change password</CardTitle>
        <CardDescription>
          Changing your password signs you out of every other session.
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
              name="old_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current password</FormLabel>
                  <FormControl>
                    <PasswordInput autoComplete="current-password" {...field} />
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
                    <PasswordInput autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirm_new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm new password</FormLabel>
                  <FormControl>
                    <PasswordInput autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              variant="outline"
              disabled={form.formState.isSubmitting}
              className="rounded-full"
            >
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Change password
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

export default function ProfilePage() {
  const meQuery = useMeQuery()

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="space-y-1">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Account</p>
        <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">
          Profile &amp; settings
        </h1>
      </div>
      {meQuery.isError ? (
        <ErrorState
          description="We couldn't load your profile. Check your connection and try again."
          onRetry={() => meQuery.refetch()}
        />
      ) : !meQuery.data ? (
        <>
          <CardSkeleton />
          <CardSkeleton />
        </>
      ) : (
        <>
          <ProfileForm user={meQuery.data} />
          <ChangePasswordForm />
        </>
      )}
    </div>
  )
}

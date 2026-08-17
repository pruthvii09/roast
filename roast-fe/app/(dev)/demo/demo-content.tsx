"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { FileWarning, Inbox, Loader2, MoreHorizontal } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { EmptyState } from "@/components/shared/empty-state"
import { ErrorState } from "@/components/shared/error-state"
import { CardSkeleton, ListSkeleton } from "@/components/shared/loading-skeletons"

const TOKENS = [
  { name: "background", className: "bg-background border border-border" },
  { name: "foreground", className: "bg-foreground" },
  { name: "muted", className: "bg-muted" },
  { name: "border", className: "bg-border" },
  { name: "card", className: "bg-card border border-border" },
  { name: "primary", className: "bg-primary" },
  { name: "destructive", className: "bg-destructive" },
  { name: "success", className: "bg-success" },
  { name: "warning", className: "bg-warning" },
] as const

const demoFormSchema = z.object({
  title: z.string().min(1, "Give your submission a title."),
  notes: z.string().max(280, "Keep it under 280 characters.").optional(),
  intensity: z.enum(["gentle", "sarcastic", "brutal", "nuclear"]),
  language: z.enum(["en", "hi", "hinglish"]),
  visibility: z.enum(["private", "link", "public"]),
  notifyByEmail: z.boolean(),
  agreeToTerms: z.boolean().refine((value) => value === true, {
    message: "You must agree before submitting.",
  }),
})

type DemoFormValues = z.infer<typeof demoFormSchema>

function Section({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {children}
    </section>
  )
}

export function DemoContent() {
  const form = useForm<DemoFormValues>({
    resolver: zodResolver(demoFormSchema),
    defaultValues: {
      title: "",
      notes: "",
      intensity: "sarcastic",
      language: "en",
      visibility: "private",
      notifyByEmail: true,
      agreeToTerms: false,
    },
  })

  function onSubmit(values: DemoFormValues) {
    toast.success("Form is valid", { description: `"${values.title}" — ${values.intensity}` })
  }

  return (
    <div className="space-y-16">
      <Section title="Tokens" description="The full CSS-variable palette — everything else on this page is built from these.">
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
          {TOKENS.map((token) => (
            <div key={token.name} className="space-y-1.5">
              <div className={`h-12 rounded-lg ${token.className}`} />
              <p className="text-xs text-muted-foreground">{token.name}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Typography">
        <div className="space-y-2">
          <h1 className="text-4xl font-semibold tracking-tight text-foreground">Heading 1</h1>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">Heading 2</h2>
          <h3 className="text-xl font-semibold tracking-tight text-foreground">Heading 3</h3>
          <h4 className="text-base font-semibold text-foreground">Heading 4</h4>
          <p className="text-base text-foreground">
            Body copy sits at a comfortable reading size with generous line height for longer roast feedback.
          </p>
          <p className="text-sm text-muted-foreground">Muted small text — captions, timestamps, helper copy.</p>
        </div>
      </Section>

      <Section title="Buttons">
        <div className="flex flex-wrap items-center gap-2">
          <Button>Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="link">Link</Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
          <Button size="icon" aria-label="More">
            <MoreHorizontal />
          </Button>
          <Button disabled>Disabled</Button>
        </div>
      </Section>

      <Section title="Form" description="React Hook Form + Zod, wired through the shared Form primitives.">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="max-w-md space-y-5">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="My resume, roasted" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Anything the roaster should know?" {...field} />
                  </FormControl>
                  <FormDescription>Optional, up to 280 characters.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="intensity"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Intensity</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose an intensity" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="gentle">Gentle</SelectItem>
                      <SelectItem value="sarcastic">Sarcastic</SelectItem>
                      <SelectItem value="brutal">Brutal</SelectItem>
                      <SelectItem value="nuclear">Nuclear</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="language"
              render={({ field }) => (
                <FormItem className="gap-3">
                  <FormLabel>Language</FormLabel>
                  <FormControl>
                    <RadioGroup
                      value={field.value}
                      onValueChange={field.onChange}
                      className="grid-flow-col justify-start gap-6"
                    >
                      {(["en", "hi", "hinglish"] as const).map((value) => (
                        <label key={value} className="flex items-center gap-2 text-sm">
                          <RadioGroupItem value={value} />
                          {value === "en" ? "English" : value === "hi" ? "Hindi" : "Hinglish"}
                        </label>
                      ))}
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="notifyByEmail"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between">
                  <div className="space-y-0.5">
                    <FormLabel>Email me when it&apos;s ready</FormLabel>
                    <FormDescription>Roasts usually take under a minute.</FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="agreeToTerms"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-2">
                  <FormControl>
                    <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                  <div className="space-y-0.5 leading-none">
                    <FormLabel>I can take a joke</FormLabel>
                    <FormMessage />
                  </div>
                </FormItem>
              )}
            />
            <Button type="submit">Submit</Button>
          </form>
        </Form>
      </Section>

      <Section title="Cards & badges">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>resume.pdf</CardTitle>
              <CardDescription>Uploaded 2 minutes ago</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Failed</Badge>
              <Badge variant="success">Ready</Badge>
              <Badge variant="warning">Processing</Badge>
            </CardContent>
          </Card>
          <Alert variant="destructive">
            <FileWarning className="size-4" />
            <AlertTitle>Extraction failed</AlertTitle>
            <AlertDescription>The uploaded file could not be parsed.</AlertDescription>
          </Alert>
        </div>
      </Section>

      <Section title="Dialog, tabs & menus">
        <div className="flex flex-wrap items-center gap-3">
          <Dialog>
            <DialogTrigger render={<Button variant="outline" />}>Open dialog</DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete submission?</DialogTitle>
                <DialogDescription>
                  This permanently deletes the submission and its roasts. This can&apos;t be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter showCloseButton>
                <Button variant="destructive">Delete</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <DropdownMenu>
            <DropdownMenuTrigger render={<Button variant="outline" />}>Actions</DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Rename</DropdownMenuItem>
              <DropdownMenuItem>Share</DropdownMenuItem>
              <DropdownMenuItem variant="destructive">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Tooltip>
            <TooltipTrigger render={<Button variant="ghost" />}>Hover me</TooltipTrigger>
            <TooltipContent>Tooltips use the same popover surface as menus.</TooltipContent>
          </Tooltip>

          <Avatar>
            <AvatarFallback>RA</AvatarFallback>
          </Avatar>
        </div>

        <Tabs defaultValue="findings" className="max-w-md">
          <TabsList>
            <TabsTrigger value="findings">Findings</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
          </TabsList>
          <TabsContent value="findings" className="text-sm text-muted-foreground">
            Individual roast findings render here, one per category.
          </TabsContent>
          <TabsContent value="summary" className="text-sm text-muted-foreground">
            The overall verdict and score render here.
          </TabsContent>
        </Tabs>

        <div className="max-w-sm space-y-2">
          <Progress value={65} />
          <p className="text-xs text-muted-foreground">Quota usage — 65% of this week&apos;s roasts used.</p>
        </div>
      </Section>

      <Section title="Toasts">
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => toast.success("Roast ready", { description: "Your feedback is in." })}>
            Success
          </Button>
          <Button variant="outline" onClick={() => toast.error("Extraction failed", { description: "Try a different file." })}>
            Error
          </Button>
          <Button variant="outline" onClick={() => toast.warning("Quota running low", { description: "1 roast left this week." })}>
            Warning
          </Button>
          <Button variant="outline" onClick={() => toast.message("Draft saved")}>
            Message
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              toast.promise(new Promise((resolve) => setTimeout(resolve, 1500)), {
                loading: "Generating roast…",
                success: "Roast complete",
                error: "Something went wrong",
              })
            }
          >
            Promise
          </Button>
        </div>
      </Section>

      <Section title="Skeletons">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
          <CardSkeleton />
        </div>
        <ListSkeleton rows={2} />
      </Section>

      <Separator />

      <Section title="Empty & error states">
        <div className="grid gap-4 sm:grid-cols-2">
          <EmptyState
            icon={Inbox}
            title="No submissions yet"
            description="Upload a resume, website, or GitHub profile to get roasted."
            action={{ label: "New submission", onClick: () => toast.message("Not wired up yet") }}
          />
          <ErrorState
            title="Couldn't load your roasts"
            description="Check your connection and try again."
            onRetry={() => toast.message("Retried")}
          />
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading state — spinner convention for inline async actions.
        </div>
      </Section>
    </div>
  )
}

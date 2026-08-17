"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

interface FadeInProps extends React.ComponentProps<"div"> {
  delay?: number
}

function FadeIn({ className, style, delay = 0, ...props }: FadeInProps) {
  const ref = React.useRef<HTMLDivElement>(null)
  const [visible, setVisible] = React.useState(false)

  React.useEffect(() => {
    const node = ref.current
    if (!node) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      style={{
        transitionDelay: visible ? `${delay}ms` : undefined,
        ...style,
      }}
      className={cn(
        "transition-all duration-700 ease-out motion-reduce:opacity-100! motion-reduce:translate-y-0! motion-reduce:transition-none!",
        visible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
        className
      )}
      {...props}
    />
  )
}

export { FadeIn }

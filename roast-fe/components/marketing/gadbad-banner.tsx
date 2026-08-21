"use client"

import { useEffect, useRef, useState } from "react"
import { Pause, Play } from "lucide-react"

const BAR_COUNT = 64

function seededFraction(seed: number) {
  const x = Math.sin(seed) * 43758.5453
  return x - Math.floor(x)
}

const BARS = Array.from({ length: BAR_COUNT }, (_, i) => ({
  heightPercent: (0.25 + seededFraction(i * 12.9898) * 0.75) * 100,
  duration: 0.6 + seededFraction(i * 78.233) * 0.7,
  delay: (i % 9) * 0.07,
})).map((bar) => ({
  ...bar,
  heightPercent: Number(bar.heightPercent.toFixed(2)),
  duration: Number(bar.duration.toFixed(2)),
}))

export function GadbadBanner() {
  const audioRef = useRef<HTMLAudioElement>(null)
  const barsRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    const onTimeUpdate = () => {
      if (audio.duration) setProgress(audio.currentTime / audio.duration)
    }
    audio.addEventListener("timeupdate", onTimeUpdate)
    return () => audio.removeEventListener("timeupdate", onTimeUpdate)
  }, [])

  function toggle() {
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) {
      audio.pause()
    } else {
      void audio.play()
    }
    setIsPlaying((prev) => !prev)
  }

  function seek(event: React.MouseEvent<HTMLDivElement>) {
    const audio = audioRef.current
    const bars = barsRef.current
    if (!audio || !bars || !audio.duration) return
    const rect = bars.getBoundingClientRect()
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
    audio.currentTime = ratio * audio.duration
    setProgress(ratio)
  }

  const activeBars = Math.round(progress * BAR_COUNT)

  return (
    <div className="mb-10 w-full space-y-3">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/gadbad.gif"
        alt="Gadbad hai — chaos meme, because legal pages don't have to be boring"
        className="block h-auto w-full rounded-2xl border border-border shadow-sm"
      />

      <audio
        ref={audioRef}
        src="/gadba.mp3"
        preload="none"
        onEnded={() => {
          setIsPlaying(false)
          setProgress(0)
        }}
      />

      <div className="flex w-full items-center gap-3 rounded-2xl border border-border bg-card px-3 py-2.5">
        <button
          type="button"
          onClick={toggle}
          aria-pressed={isPlaying}
          aria-label={isPlaying ? "Pause" : "Play"}
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105 active:scale-95"
        >
          {isPlaying ? (
            <Pause className="size-4" />
          ) : (
            <Play className="size-4 translate-x-px" />
          )}
        </button>

        <div
          ref={barsRef}
          onClick={seek}
          className="flex h-8 flex-1 cursor-pointer items-center gap-[2px]"
        >
          {BARS.map((bar, i) => (
            <span
              key={i}
              className="w-full min-w-[2px] origin-bottom rounded-full"
              style={{
                height: `${bar.heightPercent}%`,
                backgroundColor:
                  i < activeBars
                    ? "var(--color-primary)"
                    : "color-mix(in oklch, var(--color-muted-foreground), transparent 65%)",
                animationName: "gadbad-wave",
                animationDuration: `${bar.duration}s`,
                animationTimingFunction: "ease-in-out",
                animationDelay: `${bar.delay}s`,
                animationIterationCount: "infinite",
                animationPlayState: isPlaying ? "running" : "paused",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

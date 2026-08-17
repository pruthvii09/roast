"use client"

import { useState } from "react"
import { File as FileIcon, UploadCloud, X } from "lucide-react"

import { Progress } from "@/components/ui/progress"
import { ACCEPTED_RESUME_EXTENSIONS } from "@/components/roast-flow/copy"
import { cn } from "@/lib/utils"

interface ResumeDropzoneProps {
  file: File | null
  onFileChange: (file: File | null) => void
  uploadProgress: number | null
  id: string
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function ResumeDropzone({ file, onFileChange, uploadProgress, id }: ResumeDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const isUploading = uploadProgress !== null

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    if (isUploading) return
    const dropped = event.dataTransfer.files?.[0]
    if (dropped) onFileChange(dropped)
  }

  if (file) {
    return (
      <div className="rounded-2xl border border-border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <FileIcon className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
            <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
          </div>
          {!isUploading ? (
            <button
              type="button"
              onClick={() => onFileChange(null)}
              aria-label="Remove file"
              className="flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          ) : null}
        </div>
        {isUploading ? (
          <div className="mt-3 space-y-1.5">
            <Progress value={uploadProgress} aria-label="Upload progress" />
            <p className="text-xs text-muted-foreground" aria-live="polite">
              Uploading… {uploadProgress}%
            </p>
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed p-8 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border"
      )}
    >
      <div className="flex size-10 items-center justify-center rounded-xl bg-muted text-muted-foreground">
        <UploadCloud className="size-5" />
      </div>
      <p className="text-sm font-medium text-foreground">Drag and drop your resume here</p>
      <p className="text-xs text-muted-foreground">or</p>
      <label
        htmlFor={id}
        className="inline-flex cursor-pointer items-center rounded-full border border-border bg-background px-4 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-within:ring-3 focus-within:ring-ring/50"
      >
        Browse files
        <input
          id={id}
          type="file"
          accept={ACCEPTED_RESUME_EXTENSIONS.join(",")}
          className="sr-only"
          onChange={(event) => {
            const selected = event.target.files?.[0]
            if (selected) onFileChange(selected)
            event.target.value = ""
          }}
        />
      </label>
      <p className="mt-1 text-xs text-muted-foreground">PDF, DOC, or DOCX — up to 10MB.</p>
    </div>
  )
}

export { ResumeDropzone }

"use client"

import { useRef, useState } from "react"
import { Textarea } from "@/components/ui/textarea"
import { cn, deriveProjectName } from "@/lib/utils"
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea"
import { ArrowUpIcon, Paperclip, XIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

import NewProjectDialog from "./new-project-dialog"
import { useChat } from "@/context/chat-store"
import { useRouter } from "next/navigation"
import { useCreateProject } from "@/hooks/query/use-create-project"

const DATASET_ACCEPT = ".csv,.xlsx,.xls,.json,.parquet,.tsv"

export function ChatInput() {
  const router = useRouter()
  const [value, setValue] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  })
  const { sendMessage, isBusy } = useChat()
  const { mutateAsync: createProject, isPending: isCreatingProject } =
    useCreateProject()

  const isSubmitting = isBusy || isCreatingProject

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0]
    if (!selected) return
    setFile(selected)
    e.target.value = ""
  }

  function removeFile() {
    setFile(null)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  async function handleSubmit() {
    const question = value.trim()
    if (!question || isSubmitting) return
    try {
      let projectId: string | undefined

      if (file) {
        const { project } = await createProject({
          project_name: deriveProjectName(question),
          file,
        })
        projectId = project.id
      }

      const response = await sendMessage(question, projectId)

      router.push(`/projects/${projectId ?? response.project.id}`)
    } catch (err) {
      console.error("Failed to send message", err)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col items-center space-y-4 p-4 py-24 sm:space-y-8">
      <h1 className="text-center text-2xl font-bold text-foreground sm:text-4xl">
        Your AI Data Analyst, ready to analize.
      </h1>
      <div className="w-full">
        <div className="relative rounded-xl border border-border bg-card">
          <input
            ref={fileInputRef}
            type="file"
            accept={DATASET_ACCEPT}
            onChange={handleFileChange}
            className="hidden"
          />
          {file && (
            <div className="flex items-center gap-2 border-b border-border px-4 py-2 text-sm text-muted-foreground">
              <span className="truncate">{file.name}</span>
              <button
                type="button"
                onClick={removeFile}
                className="ml-auto cursor-pointer"
                aria-label="Remove file"
              >
                <XIcon className="h-4 w-4" />
              </button>
            </div>
          )}
          <div className="overflow-y-auto">
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => {
                setValue(e.target.value)
                adjustHeight()
              }}
              disabled={isSubmitting}
              onKeyDown={handleKeyDown}
              placeholder="Ask AI a question..."
              className={cn(
                "w-full px-4 py-3",
                "resize-none",
                "bg-transparent",
                "border-none",
                "text-sm",
                "focus:outline-none",
                "focus-visible:ring-0 focus-visible:ring-offset-0",
                "placeholder:text-sm",
                "min-h-[60px]"
              )}
              style={{
                overflow: "hidden",
              }}
            />
          </div>

          <div className="flex items-center justify-between p-3">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="group flex cursor-pointer items-center gap-1 rounded-lg p-2 hover:bg-secondary/50"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip className="h-4 w-4" />
                <span className="hidden text-xs transition-opacity group-hover:inline">
                  Attach CSV FILE
                </span>
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <NewProjectDialog />
              <button
                type="button"
                onClick={handleSubmit}
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-1 rounded-lg border border-border px-1.5 py-1.5 text-sm transition-colors disabled:cursor-default",
                  value.trim() || !isSubmitting
                    ? "bg-white text-black"
                    : "text-zinc-400"
                )}
                disabled={!value.trim() || isSubmitting}
              >
                <ArrowUpIcon
                  className={cn(
                    "h-4 w-4",
                    value.trim() ? "text-black" : "text-zinc-400"
                  )}
                />
                <span className="sr-only">Send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInput

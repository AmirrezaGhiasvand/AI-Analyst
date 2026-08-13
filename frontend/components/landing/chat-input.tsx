"use client"

import { useState } from "react"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea"
import { ArrowUpIcon, Paperclip, PlusIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ChatInput() {
  const [value, setValue] = useState("")
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  })

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (value.trim()) {
        setValue("")
        adjustHeight(true)
      }
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col items-center space-y-4 p-4 py-24 sm:space-y-8">
      <h1 className="text-center text-2xl font-bold text-foreground sm:text-4xl">
        Your AI Data Analyst, ready to analize.
      </h1>
      <div className="w-full">
        <div className="relative rounded-xl border border-border bg-card">
          <div className="overflow-y-auto">
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => {
                setValue(e.target.value)
                adjustHeight()
              }}
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
              >
                <Paperclip className="h-4 w-4" />
                <span className="hidden text-xs transition-opacity group-hover:inline">
                  Attach CSV FILE
                </span>
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="secondary"
                className="flex cursor-pointer items-center justify-between gap-1 rounded-lg border border-dashed border-border px-2 py-1 text-sm transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                Project
              </Button>
              <button
                type="button"
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-1 rounded-lg border border-border px-1.5 py-1.5 text-sm transition-colors",
                  value.trim() ? "bg-white text-black" : "text-zinc-400"
                )}
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

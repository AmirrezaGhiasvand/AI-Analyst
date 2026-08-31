// components/main/chat-footer-form.tsx
"use client"

import { useRef, useState } from "react"
import { FileSpreadsheet, ArrowUp, PlusIcon, XIcon } from "lucide-react"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "../ui/input-group"
import {
  Attachment,
  AttachmentAction,
  AttachmentActions,
  AttachmentContent,
  AttachmentMedia,
  AttachmentTitle,
} from "../ui/attachment"
import { useChat } from "@/context/chat-store"
import { useAddToProject } from "@/hooks/query/use-add-to-project"

const DATASET_ACCEPT = ".csv,.xlsx,.xls,.json,.parquet,.tsv"

export function ChatFooterForm({ projectId }: { projectId: string }) {
  const [input, setInput] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { isBusy, sendMessage } = useChat()
  const { mutateAsync: addToProject, isPending: isUploading } =
    useAddToProject()

  const isSubmitting = isBusy || isUploading

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault()

    const message = input.trim()

    if (!message || isSubmitting) {
      return
    }

    try {
      if (file) {
        await addToProject({ project_id: projectId, file })
      }

      setFile(null)
      setInput("")
      await sendMessage(message, projectId)
    } catch (err) {
      // dataset upload or message send failed — keep the draft so the user can retry
      console.error("Failed to send message", err)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
    // Shift+Enter: no preventDefault, textarea inserts a newline as normal
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selectedFile = e.target.files?.[0]

    if (!selectedFile) {
      return
    }

    setFile(selectedFile)

    // Allow selecting the same file again after removing it.
    e.target.value = ""
  }

  function removeFile() {
    setFile(null)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept={DATASET_ACCEPT}
        onChange={handleFileChange}
        className="hidden"
      />
      {file && (
        <Attachment className="mb-1 w-full">
          <AttachmentMedia>
            <FileSpreadsheet className="size-4 text-muted-foreground" />
          </AttachmentMedia>
          <AttachmentContent>
            <AttachmentTitle>{file.name}</AttachmentTitle>
          </AttachmentContent>
          <AttachmentActions>
            <AttachmentAction
              aria-label="Remove message-renderer.tsx"
              onClick={removeFile}
            >
              <XIcon />
            </AttachmentAction>
          </AttachmentActions>
        </Attachment>
      )}
      <InputGroup className="relative rounded-xl border border-border bg-card">
        <InputGroupTextarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the AI..."
          disabled={isSubmitting}
          rows={1}
          className="min-h-0"
        />
        <InputGroupAddon align="block-end">
          <InputGroupButton
            type="button"
            variant="ghost"
            size="icon-xs"
            className={"cursor-pointer"}
            onClick={() => fileInputRef.current?.click()}
            disabled={isSubmitting}
          >
            <PlusIcon className="size-4" />
          </InputGroupButton>
          <InputGroupButton
            variant="default"
            size="icon-xs"
            className="ml-auto cursor-pointer"
            type="submit"
            disabled={!input.trim() || isSubmitting}
          >
            <ArrowUp className="size-4" />
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </form>
  )
}

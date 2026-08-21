"use client"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import {
  ArrowUp,
  FileSpreadsheet,
  GripVertical,
  PlusIcon,
  XIcon,
} from "lucide-react"
import { ComponentProps, CSSProperties, useRef, useState } from "react"
import useHandleResizeSidebar from "@/hooks/use-handle-resize-sidebar"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "../ui/input-group"
import ChatEmptyPlaceholder from "./chat-empty-placeholder"
import AIChatProvider from "./ai-chat-provider"
import { useSendMessage } from "@/hooks/query/use-send-message"
import {
  Attachment,
  AttachmentAction,
  AttachmentActions,
  AttachmentContent,
  AttachmentMedia,
  AttachmentTitle,
} from "../ui/attachment"

type Props = ComponentProps<typeof Sidebar> & {
  projectId: string
}

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  generated_code?: string
  route?: string
  execution_result?: string
  chart?: Record<string, unknown>
  created_at?: string
}

const DATASET_ACCEPT = ".csv,.xlsx,.xls,.json,.parquet,.tsv"

export function AIChatSidebar({ projectId, className, ...props }: Props) {
  const { isResizing, handlePointerDown, width } = useHandleResizeSidebar()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [file, setFile] = useState<File | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const sendMessage = useSendMessage(projectId)
  const isBusy = sendMessage.isPending

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const message = input.trim()

    if (!message || isBusy) {
      return
    }

    // Immediately show the user's message.
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: message,
      },
    ])

    setInput("")

    sendMessage.mutate(
      {
        question: message,
      },
      {
        onSuccess: (response) => {
          setMessages((prev) => [
            ...prev,
            {
              id: response.message_id,
              role: "assistant",
              content: response.content,
              generated_code: response.generated_code,
              route: response.route,
              execution_result: response.execution_result,
              chart: response.chart,
              created_at: response.created_at,
            },
          ])
          setFile(null)
        },
      }
    )
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
    <Sidebar
      collapsible="none"
      className={cn(
        "sticky top-0 hidden h-svh border-r md:flex",
        "relative", // needed so the handle can be absolutely positioned
        className
      )}
      style={{ "--sidebar-width": `${width}px` } as CSSProperties}
      {...props}
    >
      {/* resize handle */}
      <div
        role="separator"
        aria-orientation="vertical"
        onPointerDown={handlePointerDown}
        className={cn(
          "group/handle absolute inset-y-0 inset-e-0 z-20 w-4 translate-x-1/2",
          "cursor-col-resize touch-none select-none",
          // thin line, only visible on hover/drag
          "after:absolute after:inset-y-0 after:inset-e-1/2 after:w-px after:translate-x-1/2",
          "after:bg-transparent hover:after:bg-border",
          isResizing && "after:bg-primary"
        )}
      >
        {/* grip pill, centered vertically */}
        <div
          className={cn(
            "absolute inset-e-1/2 top-1/2 translate-x-1/2 -translate-y-1/2",
            "flex h-10 w-4 items-center justify-center rounded-full border bg-border",
            "z-50 opacity-0 transition-opacity duration-150",
            "group-hover/handle:opacity-100",
            isResizing && "border-primary bg-primary opacity-100"
          )}
        >
          <GripVertical
            className={cn(
              "size-3 text-muted-foreground",
              isResizing && "text-primary-foreground"
            )}
          />
        </div>
      </div>

      <SidebarHeader>
        <SidebarTrigger />
      </SidebarHeader>

      <SidebarContent className="h-full px-3 py-2">
        {messages.length === 0 ? (
          <ChatEmptyPlaceholder />
        ) : (
          <AIChatProvider messages={messages} isBusy={isBusy} />
        )}
      </SidebarContent>
      <SidebarFooter className="relative px-2 py-1">
        <div className="pointer-events-none absolute inset-x-0 -top-12 h-12 bg-linear-to-t from-sidebar to-transparent" />

        <div className="relative rounded-xl border border-border bg-card">
          <form onSubmit={handleSubmit} className="w-full">
            <input
              ref={fileInputRef}
              type="file"
              accept={DATASET_ACCEPT}
              onChange={handleFileChange}
              className="hidden"
            />
            {file && (
              <Attachment className="w-full">
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
            <InputGroup>
              <InputGroupInput
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask the AI..."
                disabled={isBusy}
              />
              <InputGroupAddon align="inline-start">
                <InputGroupButton
                  type="button"
                  variant="ghost"
                  size="icon-xs"
                  className={"cursor-pointer"}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isBusy}
                >
                  <PlusIcon className="size-4" />
                </InputGroupButton>
              </InputGroupAddon>
              <InputGroupAddon align="inline-end">
                <InputGroupButton
                  variant="default"
                  size="icon-xs"
                  className="ml-auto"
                  type="submit"
                  disabled={!input.trim() || isBusy}
                >
                  <ArrowUp className="size-4" />
                </InputGroupButton>
              </InputGroupAddon>
            </InputGroup>
          </form>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

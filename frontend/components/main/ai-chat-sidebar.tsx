"use client"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { GripVertical } from "lucide-react"
import { ComponentProps, CSSProperties } from "react"
import useHandleResizeSidebar from "@/hooks/use-handle-resize-sidebar"
import ChatEmptyPlaceholder from "./chat-empty-placeholder"
import AIChatProvider from "./ai-chat-provider"
import { useChat } from "@/context/chat-store"
import { ChatFooterForm } from "./ai-chat-footer"

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

export function AIChatSidebar({ projectId, className, ...props }: Props) {
  const { isResizing, handlePointerDown, width } = useHandleResizeSidebar()

  const { messages, isBusy } = useChat()

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
        <ChatFooterForm projectId={projectId} />
      </SidebarFooter>
    </Sidebar>
  )
}
